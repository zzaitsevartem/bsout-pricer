from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.model.user import Subscription, User
from src.modules.products.model.product import Product
from src.modules.stores.model.store import Store


class AdminService:

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        users_count = await db.execute(select(func.count(User.id)))
        subs_count = await db.execute(
            select(func.count(Subscription.id)).where(Subscription.is_active.is_(True))
        )
        products_count = await db.execute(select(func.count(Product.id)))
        stores_count = await db.execute(select(func.count(Store.id)))

        return {
            "total_users": users_count.scalar() or 0,
            "active_subscriptions": subs_count.scalar() or 0,
            "total_products": products_count.scalar() or 0,
            "total_stores": stores_count.scalar() or 0,
        }

    @staticmethod
    async def get_users(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[User]:
        result = await db.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def toggle_user_active(db: AsyncSession, user: User) -> User:
        user.is_active = not user.is_active
        await db.flush()
        return user
