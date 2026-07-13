from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.auth.model.user import Subscription, User
from src.modules.auth.schema.user import (
    SubscriptionCreateRequest,
    SubscriptionResponse,
    UserResponse,
    UserUpdateRequest,
)
from src.modules.auth.service.auth import get_user_by_id
from src.modules.shared import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.phone is not None:
        current_user.phone = body.phone
    if body.company is not None:
        current_user.company = body.company

    await db.flush()
    return current_user


@router.get("/me/subscription", response_model=SubscriptionResponse)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.is_active.is_(True),
        ).order_by(Subscription.created_at.desc()).limit(1)
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )
    return subscription


@router.post("/me/subscription", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    body: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime, timedelta, timezone

    active_result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.is_active.is_(True),
        )
    )
    existing_active = active_result.scalar_one_or_none()
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an active subscription",
        )

    now = datetime.now(timezone.utc)
    duration_days = 30 if body.plan.value != "trial" else 10

    subscription = Subscription(
        user_id=current_user.id,
        plan=body.plan,
        start_date=now,
        end_date=now + timedelta(days=duration_days),
        is_active=True,
        auto_renew=True,
    )
    db.add(subscription)
    await db.flush()
    return subscription
