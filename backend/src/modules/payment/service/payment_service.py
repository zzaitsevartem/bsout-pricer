from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.model.user import PlanEnum, Subscription


class PaymentService:
    PLAN_PRICES = {
        PlanEnum.trial: Decimal("0"),
        PlanEnum.basic: Decimal("399"),
        PlanEnum.advanced: Decimal("499"),
    }

    @staticmethod
    async def create_subscription(
        db: AsyncSession, user_id: int, plan: PlanEnum
    ) -> Subscription:
        now = datetime.now(timezone.utc)
        duration_days = 10 if plan == PlanEnum.trial else 30

        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.is_active = False

        subscription = Subscription(
            user_id=user_id,
            plan=plan,
            start_date=now,
            end_date=now + timedelta(days=duration_days),
            is_active=True,
            auto_renew=True,
        )
        db.add(subscription)
        await db.flush()
        return subscription

    @staticmethod
    async def cancel_subscription(db: AsyncSession, subscription: Subscription) -> Subscription:
        subscription.is_active = False
        subscription.auto_renew = False
        await db.flush()
        return subscription
