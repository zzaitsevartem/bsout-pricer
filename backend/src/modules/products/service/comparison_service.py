from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.model.catalog import Brand, Device, PartType, QualityTier
from src.modules.products.model.product import (
    Cluster,
    OfferPriceHistory,
    Product,
    StoreOffer,
)
from src.modules.stores.model.store import Store

CATALOG_SORT_OPTIONS = ("min_price_asc", "min_price_desc")
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
            func.min(StoreOffer.price_opt).label("min_price_opt"),
            func.count(StoreOffer.id).label("offers_count"),
            func.count(func.distinct(StoreOffer.store_id)).label("stores_count"),
            func.array_agg(func.distinct(Store.slug)).label("store_slugs"),
        )
        .join(Store, Store.id == StoreOffer.store_id)
        .where(StoreOffer.is_active.is_(True))
        .where(StoreOffer.product_id.is_not(None))
        .group_by(StoreOffer.product_id)
        .subquery()
    )


def _ref(entity, fields: tuple[str, ...]) -> dict | None:
    if entity is None:
        return None
    return {name: getattr(entity, name) for name in fields}


def _brand_ref(brand) -> dict | None:
    return _ref(brand, ("id", "name", "slug"))


def _device_ref(device) -> dict | None:
    return _ref(device, ("id", "name", "model_key", "brand_id"))


def _part_type_ref(part_type) -> dict | None:
    return _ref(part_type, ("id", "code", "name_ru"))


def _quality_ref(quality) -> dict | None:
    return _ref(quality, ("id", "code", "name_ru", "rank"))


def _cluster_ref(cluster) -> dict | None:
    if cluster is None:
        return None
    return {
        "id": cluster.id,
        "device_id": cluster.device_id,
        "part_type_id": cluster.part_type_id,
        "offers_count": cluster.offers_count,
        "min_price_retail": _money(cluster.min_price_retail),
        "min_price_opt": _money(cluster.min_price_opt),
    }


def _catalog_item(row) -> dict:
    product = row.Product
    return {
        "id": product.id,
        "canonical_key": product.canonical_key,
        "canonical_name": product.canonical_name,
        "cluster_id": product.cluster_id,
        "key_attrs": product.key_attrs,
        "brand": _brand_ref(row.Brand),
        "device": _device_ref(row.Device),
        "part_type": _part_type_ref(row.PartType),
        "quality_tier": _quality_ref(row.QualityTier),
        "min_price_retail": _money(row.min_price_retail),
        "min_price_opt": _money(row.min_price_opt),
        "offers_count": row.offers_count or 0,
        "stores_count": row.stores_count or 0,
        "store_slugs": sorted(row.store_slugs or []),
    }


class ComparisonService:
    @staticmethod
    def _apply_filters(
        stmt,
        query: str,
        device_id: int | None,
        part_type_id: int | None,
        quality_tier_id: int | None,
    ):
        normalized = (query or "").strip()
        if normalized:
            stmt = stmt.where(Product.canonical_name.ilike(f"%{normalized}%"))
        if device_id is not None:
            stmt = stmt.where(Cluster.device_id == device_id)
        if part_type_id is not None:
            stmt = stmt.where(Cluster.part_type_id == part_type_id)
        if quality_tier_id is not None:
            stmt = stmt.where(Product.quality_tier_id == quality_tier_id)
        return stmt

    @staticmethod
    async def search_catalog(
        db: AsyncSession,
        query: str = "",
        device_id: int | None = None,
        part_type_id: int | None = None,
        quality_tier_id: int | None = None,
        sort_by: str = "min_price_asc",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[dict], int]:
        agg = _offer_aggregate_subquery()

        count_stmt = (
            select(func.count(Product.id))
            .select_from(Product)
            .outerjoin(Cluster, Cluster.id == Product.cluster_id)
        )
        count_stmt = ComparisonService._apply_filters(
            count_stmt, query, device_id, part_type_id, quality_tier_id
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(
                Product,
                Cluster,
                QualityTier,
                Brand,
                Device,
                PartType,
                agg.c.min_price_retail,
                agg.c.min_price_opt,
                agg.c.offers_count,
                agg.c.stores_count,
                agg.c.store_slugs,
            )
            .select_from(Product)
            .outerjoin(Cluster, Cluster.id == Product.cluster_id)
            .outerjoin(QualityTier, QualityTier.id == Product.quality_tier_id)
            .outerjoin(Brand, Brand.id == Product.brand_id)
            .outerjoin(Device, Device.id == Cluster.device_id)
            .outerjoin(PartType, PartType.id == Cluster.part_type_id)
            .outerjoin(agg, agg.c.product_id == Product.id)
        )
        stmt = ComparisonService._apply_filters(
            stmt, query, device_id, part_type_id, quality_tier_id
        )

        if sort_by == "min_price_desc":
            order = agg.c.min_price_retail.desc().nullslast()
        else:
            order = agg.c.min_price_retail.asc().nullslast()

        offset = (page - 1) * per_page
        stmt = stmt.order_by(order, Product.id.asc()).offset(offset).limit(per_page)

        rows = (await db.execute(stmt)).all()
        return [_catalog_item(row) for row in rows], total

    @staticmethod
    async def _load_product_row(db: AsyncSession, product_id: int):
        agg = _offer_aggregate_subquery()
        stmt = (
            select(
                Product,
                Cluster,
                QualityTier,
                Brand,
                Device,
                PartType,
                agg.c.min_price_retail,
                agg.c.min_price_opt,
                agg.c.offers_count,
                agg.c.stores_count,
                agg.c.store_slugs,
            )
            .select_from(Product)
            .outerjoin(Cluster, Cluster.id == Product.cluster_id)
            .outerjoin(QualityTier, QualityTier.id == Product.quality_tier_id)
            .outerjoin(Brand, Brand.id == Product.brand_id)
            .outerjoin(Device, Device.id == Cluster.device_id)
            .outerjoin(PartType, PartType.id == Cluster.part_type_id)
            .outerjoin(agg, agg.c.product_id == Product.id)
            .where(Product.id == product_id)
        )
        return (await db.execute(stmt)).first()

    @staticmethod
    async def _load_offers(db: AsyncSession, product_id: int) -> list[dict]:
        stmt = (
            select(StoreOffer, Store)
            .join(Store, Store.id == StoreOffer.store_id)
            .where(StoreOffer.product_id == product_id)
            .where(StoreOffer.is_active.is_(True))
            .order_by(StoreOffer.price_retail.asc(), StoreOffer.id.asc())
        )
        rows = (await db.execute(stmt)).all()

        offers = []
        for offer, store in rows:
            offers.append(
                {
                    "id": offer.id,
                    "store_id": offer.store_id,
                    "source_sku": offer.source_sku,
                    "title": offer.title,
                    "price_retail": _money(offer.price_retail),
                    "price_opt": _money(offer.price_opt),
                    "price_old": _money(offer.price_old),
                    "currency": offer.currency,
                    "stock_status": offer.stock_status,
                    "stock_qty": offer.stock_qty,
                    "url": offer.url,
                    "match_status": offer.match_status,
                    "match_confidence": offer.match_confidence,
                    "last_seen_at": offer.last_seen_at,
                    "price_changed_at": offer.price_changed_at,
                    "is_cheapest": False,
                    "store": {"id": store.id, "name": store.name, "slug": store.slug},
                }
            )

        if offers:
            cheapest = offers[0]["price_retail"]
            for item in offers:
                item["is_cheapest"] = item["price_retail"] == cheapest

        return offers

    @staticmethod
    def _build_stats(offers: list[dict]) -> dict:
        if not offers:
            return {
                "offers_count": 0,
                "stores_count": 0,
                "min_price_retail": None,
                "max_price_retail": None,
                "avg_price_retail": None,
                "min_price_opt": None,
                "spread_abs": None,
                "spread_pct": None,
            }

        retail = [item["price_retail"] for item in offers]
        opt = [item["price_opt"] for item in offers if item["price_opt"] is not None]
        minimum = min(retail)
        maximum = max(retail)
        average = _money(sum(retail) / Decimal(len(retail)))
        spread_abs = _money(maximum - minimum)
        spread_pct = None
        if minimum > 0:
            spread_pct = float(
                (spread_abs / minimum * Decimal(100)).quantize(CENTS, rounding=ROUND_HALF_UP)
            )

        return {
            "offers_count": len(offers),
            "stores_count": len({item["store_id"] for item in offers}),
            "min_price_retail": minimum,
            "max_price_retail": maximum,
            "avg_price_retail": average,
            "min_price_opt": min(opt) if opt else None,
            "spread_abs": spread_abs,
            "spread_pct": spread_pct,
        }

    @staticmethod
    async def _load_alternatives(
        db: AsyncSession, cluster_id: int | None, product_id: int
    ) -> list[dict]:
        if cluster_id is None:
            return []

        agg = _offer_aggregate_subquery()
        stmt = (
            select(
                Product,
                QualityTier,
                agg.c.min_price_retail,
                agg.c.min_price_opt,
                agg.c.offers_count,
                agg.c.stores_count,
            )
            .select_from(Product)
            .outerjoin(QualityTier, QualityTier.id == Product.quality_tier_id)
            .outerjoin(agg, agg.c.product_id == Product.id)
            .where(Product.cluster_id == cluster_id)
            .where(Product.id != product_id)
            .order_by(agg.c.min_price_retail.asc().nullslast(), Product.id.asc())
        )
        rows = (await db.execute(stmt)).all()

        return [
            {
                "product_id": row.Product.id,
                "canonical_key": row.Product.canonical_key,
                "canonical_name": row.Product.canonical_name,
                "quality_tier": _quality_ref(row.QualityTier),
                "min_price_retail": _money(row.min_price_retail),
                "min_price_opt": _money(row.min_price_opt),
                "offers_count": row.offers_count or 0,
                "stores_count": row.stores_count or 0,
            }
            for row in rows
        ]

    @staticmethod
    async def get_comparison(db: AsyncSession, product_id: int) -> dict | None:
        row = await ComparisonService._load_product_row(db, product_id)
        if row is None:
            return None

        offers = await ComparisonService._load_offers(db, product_id)
        alternatives = await ComparisonService._load_alternatives(
            db, row.Product.cluster_id, product_id
        )

        return {
            "product": _catalog_item(row),
            "cluster": _cluster_ref(row.Cluster),
            "offers": offers,
            "stats": ComparisonService._build_stats(offers),
            "alternatives": alternatives,
        }

    @staticmethod
    async def product_exists(db: AsyncSession, product_id: int) -> bool:
        result = await db.execute(select(Product.id).where(Product.id == product_id))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_price_history(
        db: AsyncSession, product_id: int, days: int = 90
    ) -> list[dict] | None:
        if not await ComparisonService.product_exists(db, product_id):
            return None

        since = datetime.now(timezone.utc) - timedelta(days=days)
        day = func.date(func.timezone("UTC", OfferPriceHistory.recorded_at)).label("day")

        stmt = (
            select(
                day,
                func.min(OfferPriceHistory.price_retail).label("min_price_retail"),
                func.max(OfferPriceHistory.price_retail).label("max_price_retail"),
                func.avg(OfferPriceHistory.price_retail).label("avg_price_retail"),
                func.count(func.distinct(StoreOffer.store_id)).label("stores_count"),
            )
            .select_from(OfferPriceHistory)
            .join(StoreOffer, StoreOffer.id == OfferPriceHistory.offer_id)
            .where(StoreOffer.product_id == product_id)
            .where(OfferPriceHistory.recorded_at >= since)
            .group_by(day)
            .order_by(day)
        )
        rows = (await db.execute(stmt)).all()

        return [
            {
                "day": row.day,
                "min_price_retail": _money(row.min_price_retail),
                "max_price_retail": _money(row.max_price_retail),
                "avg_price_retail": _money(row.avg_price_retail),
                "stores_count": row.stores_count or 0,
            }
            for row in rows
        ]
