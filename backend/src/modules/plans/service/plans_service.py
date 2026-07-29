from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.plans.model.plan import Plan


class PlanService:
    @staticmethod
    async def get_all(db: AsyncSession) -> list[Plan]:
        result = await db.execute(
            select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.id)
        )
        return list(result.scalars().all())
