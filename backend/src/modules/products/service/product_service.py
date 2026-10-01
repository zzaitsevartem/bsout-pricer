from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.modules.products.model.product import OfferPriceHistory, StoreOffer
from src.modules.stores.model.store import Store


class ProductService:
    @staticmethod
    async def _normalize_query(text: str) -> str:
        return text.lower().strip()

    @staticmethod
    async def search(
        db: AsyncSession,
        query: str,
        store_slug: str | None = None,
        category_slug: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
        sort_by: str = "price_asc",
        page: int = 1,
        per_page: int = 20,
        fuzzy: bool = False,
    ) -> tuple[list[StoreOffer], int]:
        filtered = select(StoreOffer).where(StoreOffer.is_active.is_(True))

        normalized = await ProductService._normalize_query(query)
        if normalized and fuzzy:
            filtered = filtered.where(StoreOffer.normalized_title.op("%")(normalized))
        elif normalized:
            filtered = filtered.where(StoreOffer.normalized_title.ilike(f"%{normalized}%"))

        if store_slug:
            store_subq = select(Store.id).where(Store.slug == store_slug).scalar_subquery()
            filtered = filtered.where(StoreOffer.store_id.in_(store_subq))

        if category_slug:
            from src.modules.categories.model.category import Category

            cat_subq = select(Category.id).where(Category.slug == category_slug).scalar_subquery()
            filtered = filtered.where(StoreOffer.category_id.in_(cat_subq))

        if min_price is not None:
            filtered = filtered.where(StoreOffer.price_retail >= min_price)
        if max_price is not None:
            filtered = filtered.where(StoreOffer.price_retail <= max_price)
        if in_stock is True:
            filtered = filtered.where(StoreOffer.stock_status.in_(("in_stock", "low")))
        elif in_stock is False:
            filtered = filtered.where(StoreOffer.stock_status == "out")

        total_result = await db.execute(select(func.count()).select_from(filtered.subquery()))
        total = total_result.scalar() or 0

        sort_map = {
            "price_asc": StoreOffer.price_retail.asc(),
            "price_desc": StoreOffer.price_retail.desc(),
            "date": StoreOffer.last_seen_at.desc(),
        }
        if normalized and fuzzy:
            order = func.similarity(StoreOffer.normalized_title, normalized).desc()
        else:
            order = sort_map.get(sort_by, StoreOffer.price_retail.asc())

        offset = (page - 1) * per_page
        result = await db.execute(filtered.order_by(order).offset(offset).limit(per_page))
        offers = list(result.scalars().all())

        return offers, total

    @staticmethod
    async def get_by_id(db: AsyncSession, offer_id: int) -> StoreOffer | None:
        result = await db.execute(
            select(StoreOffer)
            .options(joinedload(StoreOffer.price_history))
            .where(StoreOffer.id == offer_id)
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_price_history(db: AsyncSession, offer_id: int) -> list[OfferPriceHistory]:
        result = await db.execute(
            select(OfferPriceHistory)
            .where(OfferPriceHistory.offer_id == offer_id)
            .order_by(OfferPriceHistory.recorded_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, data: dict) -> StoreOffer:
        payload = dict(data)
        if not payload.get("normalized_title"):
            payload["normalized_title"] = await ProductService._normalize_query(
                payload.get("title", "")
            )

        offer = StoreOffer(**payload)
        db.add(offer)
        await db.flush()

        history = OfferPriceHistory(
            offer_id=offer.id,
            price_retail=offer.price_retail,
            price_opt=offer.price_opt,
            stock_status=offer.stock_status,
        )
        db.add(history)
        await db.flush()

        return offer

    @staticmethod
    async def find_cheapest(db: AsyncSession, query: str) -> StoreOffer | None:
        normalized = await ProductService._normalize_query(query)
        result = await db.execute(
            select(StoreOffer)
            .where(StoreOffer.is_active.is_(True))
            .where(StoreOffer.normalized_title.ilike(f"%{normalized}%"))
            .order_by(StoreOffer.price_retail.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()
