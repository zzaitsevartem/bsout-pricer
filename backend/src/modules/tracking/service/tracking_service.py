from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.products.model.product import Product, StoreOffer
from src.modules.products.service.comparison_service import ComparisonService
from src.modules.tracking.model.tracking import TrackedProduct

CENTS = Decimal("0.01")


def _money(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def _offer_aggregate_subquery():
    return (
        select(
            StoreOffer.product_id.label("product_id"),
            func.min(StoreOffer.price_retail).label("min_price_retail"),
            func.count(func.distinct(StoreOffer.store_id)).label("stores_count"),
        )
        .where(StoreOffer.is_active.is_(True))
        .where(StoreOffer.product_id.is_not(None))
        .group_by(StoreOffer.product_id)
        .subquery()
    )


def _build_item(
    tracked: TrackedProduct,
    canonical_key: str,
    canonical_name: str,
    current_price: Decimal | None,
    stores_count: int,
) -> dict:
    current = _money(current_price)
    baseline = _money(tracked.last_seen_price)
    target = _money(tracked.target_price)

    delta = None
    delta_pct = None
    if current is not None and baseline is not None:
        delta = _money(current - baseline)
        if baseline > 0:
            delta_pct = float((delta / baseline * Decimal(100)).quantize(CENTS, ROUND_HALF_UP))

    return {
        "id": tracked.id,
        "product_id": tracked.product_id,
        "canonical_key": canonical_key,
        "canonical_name": canonical_name,
        "target_price": target,
        "notify_on_any_drop": tracked.notify_on_any_drop,
        "is_active": tracked.is_active,
        "last_seen_price": baseline,
        "current_price": current,
        "price_delta": delta,
        "price_delta_pct": delta_pct,
        "stores_count": stores_count or 0,
        "target_reached": target is not None and current is not None and current <= target,
        "last_notified_at": tracked.last_notified_at,
        "created_at": tracked.created_at,
    }


class TrackingService:
    @staticmethod
    async def product_snapshot(db: AsyncSession, product_id: int) -> dict | None:
        comparison = await ComparisonService.get_comparison(db, product_id)
        if comparison is None:
            return None
        return {
            "canonical_key": comparison["product"]["canonical_key"],
            "canonical_name": comparison["product"]["canonical_name"],
            "min_price_retail": comparison["stats"]["min_price_retail"],
            "stores_count": comparison["stats"]["stores_count"],
        }

    @staticmethod
    async def count_active(db: AsyncSession, user_id: int) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(TrackedProduct)
            .where(TrackedProduct.user_id == user_id)
            .where(TrackedProduct.is_active.is_(True))
        )
        return result.scalar() or 0

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int, tracked_id: int) -> TrackedProduct | None:
        result = await db.execute(
            select(TrackedProduct)
            .where(TrackedProduct.id == tracked_id)
            .where(TrackedProduct.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_product(
        db: AsyncSession, user_id: int, product_id: int
    ) -> TrackedProduct | None:
        result = await db.execute(
            select(TrackedProduct)
            .where(TrackedProduct.user_id == user_id)
            .where(TrackedProduct.product_id == product_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        product_id: int,
        target_price: Decimal | None,
        last_seen_price: Decimal | None,
    ) -> TrackedProduct:
        tracked = TrackedProduct(
            user_id=user_id,
            product_id=product_id,
            target_price=target_price,
            last_seen_price=last_seen_price,
            notify_on_any_drop=True,
            is_active=True,
        )
        db.add(tracked)
        await db.flush()
        return tracked

    @staticmethod
    async def reactivate(
        db: AsyncSession,
        tracked: TrackedProduct,
        target_price: Decimal | None,
        last_seen_price: Decimal | None,
    ) -> TrackedProduct:
        tracked.is_active = True
        tracked.last_seen_price = last_seen_price
        if target_price is not None:
            tracked.target_price = target_price
        await db.flush()
        return tracked

    @staticmethod
    async def apply_update(
        db: AsyncSession, tracked: TrackedProduct, changes: dict
    ) -> TrackedProduct:
        for field in ("target_price", "notify_on_any_drop", "is_active"):
            if field in changes:
                setattr(tracked, field, changes[field])
        await db.flush()
        return tracked

    @staticmethod
    async def delete(db: AsyncSession, tracked: TrackedProduct) -> None:
        await db.delete(tracked)
        await db.flush()

    @staticmethod
    async def build_response(
        db: AsyncSession, tracked: TrackedProduct, snapshot: dict | None = None
    ) -> dict:
        if snapshot is None:
            snapshot = await TrackingService.product_snapshot(db, tracked.product_id)
        if snapshot is None:
            snapshot = {
                "canonical_key": "",
                "canonical_name": "",
                "min_price_retail": None,
                "stores_count": 0,
            }
        return _build_item(
            tracked,
            snapshot["canonical_key"],
            snapshot["canonical_name"],
            snapshot["min_price_retail"],
            snapshot["stores_count"],
        )

    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        user_id: int,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict], int]:
        count_stmt = (
            select(func.count())
            .select_from(TrackedProduct)
            .where(TrackedProduct.user_id == user_id)
        )
        if is_active is not None:
            count_stmt = count_stmt.where(TrackedProduct.is_active.is_(is_active))
        total = (await db.execute(count_stmt)).scalar() or 0

        agg = _offer_aggregate_subquery()
        stmt = (
            select(
                TrackedProduct,
                Product.canonical_key,
                Product.canonical_name,
                agg.c.min_price_retail,
                agg.c.stores_count,
            )
            .select_from(TrackedProduct)
            .join(Product, Product.id == TrackedProduct.product_id)
            .outerjoin(agg, agg.c.product_id == TrackedProduct.product_id)
            .where(TrackedProduct.user_id == user_id)
        )
        if is_active is not None:
            stmt = stmt.where(TrackedProduct.is_active.is_(is_active))

        offset = (page - 1) * per_page
        stmt = stmt.order_by(TrackedProduct.created_at.desc(), TrackedProduct.id.desc())
        stmt = stmt.offset(offset).limit(per_page)

        rows = (await db.execute(stmt)).all()
        results = [
            _build_item(
                row.TrackedProduct,
                row.canonical_key,
                row.canonical_name,
                row.min_price_retail,
                row.stores_count or 0,
            )
            for row in rows
        ]
        return results, total
