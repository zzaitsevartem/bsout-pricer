from datetime import timedelta

import pytest
from sqlalchemy import func, select

from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.payment.service.payment_service import PaymentService

pytestmark = pytest.mark.integration


async def _make_user(db, email: str = "pay@example.com") -> User:
    user = User(email=email, password_hash="x", full_name="P", is_active=True)
    db.add(user)
    await db.flush()
    return user


async def test_trial_lasts_seven_days_per_spec(db_session):
    user = await _make_user(db_session)
    sub = await PaymentService.create_subscription(db_session, user.id, PlanEnum.trial)
    assert sub.end_date - sub.start_date == timedelta(days=7)
    assert sub.is_active is True


async def test_paid_plan_lasts_30_days(db_session):
    user = await _make_user(db_session)
    sub = await PaymentService.create_subscription(db_session, user.id, PlanEnum.basic)
    assert sub.end_date - sub.start_date == timedelta(days=30)


async def test_new_subscription_deactivates_previous(db_session):
    user = await _make_user(db_session)
    first = await PaymentService.create_subscription(db_session, user.id, PlanEnum.basic)
    second = await PaymentService.create_subscription(db_session, user.id, PlanEnum.advanced)

    assert first.is_active is False
    assert second.is_active is True

    active = (
        await db_session.execute(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
        )
    ).scalar()
    assert active == 1
