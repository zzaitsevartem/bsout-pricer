from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.auth.model.user import Subscription, User
from src.modules.shared import get_current_user


async def require_active_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Subscription:
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.is_active.is_(True),
        ).order_by(Subscription.created_at.desc()).limit(1)
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required",
        )
    return subscription
