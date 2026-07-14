from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.categories.model.category import Category


class CategoryService:

    @staticmethod
    async def get_all(db: AsyncSession) -> list[Category]:
        result = await db.execute(select(Category).order_by(Category.name))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, category_id: int) -> Category | None:
        result = await db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Category | None:
        result = await db.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, name: str, slug: str) -> Category:
        category = Category(name=name, slug=slug)
        db.add(category)
        await db.flush()
        return category

    @staticmethod
    async def update(db: AsyncSession, category: Category, data: dict) -> Category:
        for key, value in data.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)
        await db.flush()
        return category
