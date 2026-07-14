from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.stores.model.store import Store


class StoreService:

    @staticmethod
    async def get_all(db: AsyncSession, active_only: bool = True) -> list[Store]:
        query = select(Store)
        if active_only:
            query = query.where(Store.is_active.is_(True))
        query = query.order_by(Store.name)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, store_id: int) -> Store | None:
        result = await db.execute(select(Store).where(Store.id == store_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Store | None:
        result = await db.execute(select(Store).where(Store.slug == slug))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, name: str, slug: str, website_url: str, logo_url: str | None = None) -> Store:
        store = Store(name=name, slug=slug, website_url=website_url, logo_url=logo_url)
        db.add(store)
        await db.flush()
        return store

    @staticmethod
    async def update(db: AsyncSession, store: Store, data: dict) -> Store:
        for key, value in data.items():
            if value is not None and hasattr(store, key):
                setattr(store, key, value)
        await db.flush()
        return store
