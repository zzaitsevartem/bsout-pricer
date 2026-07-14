from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.auth.model.user import Subscription, User
from src.modules.payment.schema.payment import PaymentCreateRequest, PaymentResponse
from src.modules.payment.service.payment_service import PaymentService
from src.modules.shared import get_current_user

router = APIRouter(prefix="/api/payment", tags=["payment"])


@router.post("/subscribe", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(
    body: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    price = PaymentService.PLAN_PRICES.get(body.plan)
    if price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan")

    subscription = await PaymentService.create_subscription(db, current_user.id, body.plan)

    return PaymentResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        amount=price,
        plan=subscription.plan,
        status="pending" if price > 0 else "completed",
        created_at=subscription.created_at,
    )


@router.post("/cancel")
async def cancel_subscription(
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")

    await PaymentService.cancel_subscription(db, subscription)
    return {"detail": "Subscription cancelled"}
