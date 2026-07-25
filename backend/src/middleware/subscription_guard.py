from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.shared import get_current_user


async def get_active_subscription(db: AsyncSession, user_id: int) -> Subscription | None:
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.is_active.is_(True),
            Subscription.end_date > func.now(),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def require_active_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Subscription:
    subscription = await get_active_subscription(db, current_user.id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required",
        )
    return subscription


async def is_fuzzy_enabled(db: AsyncSession, user_id: int) -> bool:
    subscription = await get_active_subscription(db, user_id)
    return subscription is not None and subscription.plan == PlanEnum.advanced
