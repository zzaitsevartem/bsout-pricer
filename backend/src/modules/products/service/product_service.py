from decimal import Decimal

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.modules.cache import RedisCache
from src.modules.products.model.product import PriceHistory, Product
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
    ) -> tuple[list[Product], int]:
        base = select(Product).options(joinedload(Product.price_history))

        normalized = await ProductService._normalize_query(query)
        if normalized:
            base = base.where(Product.normalized_name.ilike(f"%{normalized}%"))

        if store_slug:
            store_subq = select(Store.id).where(Store.slug == store_slug).scalar_subquery()
            base = base.where(Product.store_id.in_(store_subq))

        if category_slug:
            from src.modules.categories.model.category import Category
            cat_subq = select(Category.id).where(Category.slug == category_slug).scalar_subquery()
            base = base.where(Product.category_id.in_(cat_subq))

        if min_price is not None:
            base = base.where(Product.price >= min_price)
        if max_price is not None:
            base = base.where(Product.price <= max_price)
        if in_stock is not None:
            base = base.where(Product.in_stock.is_(in_stock))

        sort_map = {
            "price_asc": Product.price.asc(),
            "price_desc": Product.price.desc(),
            "date": Product.last_updated.desc(),
        }
        order = sort_map.get(sort_by, Product.price.asc())
        base = base.order_by(order)

        total_query = select(Product.id).where(Product.normalized_name.ilike(f"%{normalized}%"))
        if store_slug:
            total_query = total_query.where(Product.store_id.in_(
                select(Store.id).where(Store.slug == store_slug).scalar_subquery()
            ))
        total_result = await db.execute(total_query)
        total = len(total_result.scalars().all())

        offset = (page - 1) * per_page
        result = await db.execute(base.offset(offset).limit(per_page))
        products = list(result.unique().scalars().all())

        return products, total

    @staticmethod
    async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
        result = await db.execute(
            select(Product).options(joinedload(Product.price_history)).where(Product.id == product_id)
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_price_history(db: AsyncSession, product_id: int) -> list[PriceHistory]:
        result = await db.execute(
            select(PriceHistory).where(PriceHistory.product_id == product_id).order_by(PriceHistory.recorded_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, data: dict) -> Product:
        product = Product(**data)
        db.add(product)
        await db.flush()

        history = PriceHistory(product_id=product.id, price=product.price)
        db.add(history)
        await db.flush()

        return product

    @staticmethod
    async def find_cheapest(db: AsyncSession, query: str) -> Product | None:
        normalized = await ProductService._normalize_query(query)
        result = await db.execute(
            select(Product)
            .where(Product.normalized_name.ilike(f"%{normalized}%"))
            .order_by(Product.price.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()
