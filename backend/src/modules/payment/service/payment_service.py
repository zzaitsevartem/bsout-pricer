import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.model.user import PlanEnum, Subscription
from src.modules.payment.model.payment import Payment
from src.modules.payment.service.plans import PLANS, get_plan, price_for

PENDING = "pending"
SUCCEEDED = "succeeded"
CANCELED = "canceled"
FAILED = "failed"
REFUNDED = "refunded"

DEFAULT_CURRENCY = "RUB"
DEFAULT_PROVIDER = "manual"


class PaymentService:
    PLAN_PRICES: dict[PlanEnum, Decimal] = {
        plan: definition.price for plan, definition in PLANS.items()
    }

    @staticmethod
    def build_idempotence_key(user_id: int, plan: PlanEnum, raw_key: str | None = None) -> str:
        normalized = (raw_key or "").strip()
        if normalized:
            seed = f"user:{user_id}:key:{normalized}"
        else:
            today = datetime.now(timezone.utc).date().isoformat()
            seed = f"user:{user_id}:plan:{plan.value}:day:{today}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    @staticmethod
    def describe(plan: PlanEnum) -> str:
        definition = get_plan(plan)
        return f"Подписка BScout «{definition.name_ru}» на {definition.duration_days} дн."

    @staticmethod
    async def has_successful_payment(db: AsyncSession, user_id: int) -> bool:
        result = await db.execute(
            select(func.count())
            .select_from(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.status == SUCCEEDED,
                Payment.amount > 0,
            )
        )
        return (result.scalar() or 0) > 0

    @staticmethod
    async def amount_for(db: AsyncSession, user_id: int, plan: PlanEnum) -> Decimal:
        first_payment = not await PaymentService.has_successful_payment(db, user_id)
        return price_for(plan, first_payment=first_payment)

    @staticmethod
    async def get_payment_by_key(
        db: AsyncSession, user_id: int, idempotence_key: str
    ) -> Payment | None:
        result = await db.execute(
            select(Payment).where(
                Payment.user_id == user_id,
                Payment.idempotence_key == idempotence_key,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_payment_by_reference(
        db: AsyncSession,
        provider_payment_id: str | None = None,
        idempotence_key: str | None = None,
    ) -> Payment | None:
        conditions = []
        if provider_payment_id:
            conditions.append(Payment.provider_payment_id == provider_payment_id)
        if idempotence_key:
            conditions.append(Payment.idempotence_key == idempotence_key)
        if not conditions:
            return None
        result = await db.execute(
            select(Payment).where(or_(*conditions)).order_by(Payment.id.desc()).limit(1)
        )
        return result.scalars().first()

    @staticmethod
    async def create_pending_payment(
        db: AsyncSession,
        user_id: int,
        plan: PlanEnum,
        idempotence_key: str,
        amount: Decimal,
        provider: str = DEFAULT_PROVIDER,
        confirmation_url: str | None = None,
    ) -> tuple[Payment, bool]:
        existing = await PaymentService.get_payment_by_key(db, user_id, idempotence_key)
        if existing is not None:
            return existing, False

        payment = Payment(
            user_id=user_id,
            plan=plan,
            amount=amount,
            currency=DEFAULT_CURRENCY,
            status=PENDING,
            provider=provider,
            idempotence_key=idempotence_key,
            description=PaymentService.describe(plan),
            confirmation_url=confirmation_url,
        )
        try:
            async with db.begin_nested():
                db.add(payment)
                await db.flush()
        except IntegrityError:
            existing = await PaymentService.get_payment_by_key(db, user_id, idempotence_key)
            if existing is None:
                raise
            return existing, False
        return payment, True

    @staticmethod
    async def mark_paid(
        db: AsyncSession,
        payment: Payment,
        provider_payment_id: str | None = None,
        raw: dict | None = None,
    ) -> Payment:
        if payment.status == SUCCEEDED:
            return payment

        payment.status = SUCCEEDED
        payment.paid_at = datetime.now(timezone.utc)
        if provider_payment_id:
            payment.provider_payment_id = provider_payment_id
        if raw is not None:
            payment.raw = raw

        subscription = await PaymentService.create_subscription(db, payment.user_id, payment.plan)
        payment.subscription_id = subscription.id
        await db.flush()
        return payment

    @staticmethod
    async def mark_status(
        db: AsyncSession,
        payment: Payment,
        new_status: str,
        raw: dict | None = None,
    ) -> Payment:
        payment.status = new_status
        if raw is not None:
            payment.raw = raw
        await db.flush()
        return payment

    @staticmethod
    async def list_payments(db: AsyncSession, user_id: int) -> list[Payment]:
        result = await db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc(), Payment.id.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_subscription(db: AsyncSession, user_id: int, plan: PlanEnum) -> Subscription:
        now = datetime.now(timezone.utc)
        duration_days = 10 if plan == PlanEnum.trial else get_plan(plan).duration_days

        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
            )
        )
        for existing in result.scalars().all():
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
        subscription.auto_renew = False
        end_date = subscription.end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        if end_date <= datetime.now(timezone.utc):
            subscription.is_active = False
        await db.flush()
        return subscription
