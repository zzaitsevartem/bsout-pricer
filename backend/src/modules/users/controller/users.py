from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.middleware.subscription_guard import get_active_subscription
from src.modules.auth.model.user import User
from src.modules.auth.schema.user import (
    SubscriptionCreateRequest,
    SubscriptionResponse,
    UserResponse,
    UserUpdateRequest,
)
from src.modules.auth.service.email_verification_service import require_verified_email
from src.modules.payment.service.plans import get_plan
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
    await db.refresh(current_user)
    return current_user


@router.get("/me/subscription", response_model=SubscriptionResponse)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subscription = await get_active_subscription(db, current_user.id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found",
        )
    return subscription


@router.post(
    "/me/subscription", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED
)
async def create_subscription(
    body: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_active = await get_active_subscription(db, current_user.id)
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an active subscription",
        )

    await require_verified_email(current_user)

    if get_plan(body.plan).price > 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "payment_required",
                "message": (
                    "Платные тарифы оформляются через оплату: "
                    "создайте платёж на /api/payment/subscribe."
                ),
            },
        )

    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={"code": "payment_required", "message": "Пробный период выдаётся при регистрации."},
    )
