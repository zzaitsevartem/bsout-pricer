from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from src.middleware.subscription_guard import get_active_subscription
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import (
    create_access_token,
    create_user,
    grant_trial_subscription,
    hash_password,
)
from src.modules.payment.service.plans import get_plan

pytestmark = pytest.mark.integration

PASSWORD = "s3cret-pass"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register(client, email: str) -> dict:
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": "Trial User",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _get_user(db_session, email: str) -> User:
    result = await db_session.execute(select(User).where(User.email == email))
    return result.scalar_one()


async def _count_subscriptions(db_session, user_id: int) -> int:
    result = await db_session.execute(
        select(func.count()).select_from(Subscription).where(Subscription.user_id == user_id)
    )
    return result.scalar()


async def test_register_grants_active_trial_subscription(client, db_session):
    await _register(client, "trial-new@example.com")

    user = await _get_user(db_session, "trial-new@example.com")
    subscription = await get_active_subscription(db_session, user.id)

    assert subscription is not None
    assert subscription.plan == PlanEnum.trial
    assert subscription.is_active is True
    assert user.trial_used is True


async def test_trial_duration_comes_from_plans_matrix(client, db_session):
    await _register(client, "trial-duration@example.com")

    user = await _get_user(db_session, "trial-duration@example.com")
    subscription = await get_active_subscription(db_session, user.id)

    expected_days = get_plan(PlanEnum.trial).duration_days
    actual_days = (subscription.end_date - subscription.start_date).days

    assert expected_days == 7
    assert actual_days == expected_days


async def test_trial_does_not_auto_renew(client, db_session):
    await _register(client, "trial-renew@example.com")

    user = await _get_user(db_session, "trial-renew@example.com")
    subscription = await get_active_subscription(db_session, user.id)

    assert subscription.auto_renew is False


async def test_registered_user_can_use_gated_products_immediately(client, db_session):
    body = await _register(client, "trial-access@example.com")

    resp = await client.get("/api/products", headers=_auth(body["access_token"]))

    assert resp.status_code == 200, resp.text


async def test_trial_user_has_no_fuzzy_search(client, db_session):
    from src.middleware.subscription_guard import is_fuzzy_enabled

    await _register(client, "trial-fuzzy@example.com")
    user = await _get_user(db_session, "trial-fuzzy@example.com")

    assert await is_fuzzy_enabled(db_session, user.id) is False


async def test_second_trial_is_not_granted_when_trial_used(db_session):
    user = await create_user(
        db=db_session,
        email="trial-once@example.com",
        password=PASSWORD,
        full_name="Once",
        phone=None,
        company=None,
    )

    first = await grant_trial_subscription(db_session, user)
    assert first is not None
    assert user.trial_used is True

    second = await grant_trial_subscription(db_session, user)

    assert second is None
    assert await _count_subscriptions(db_session, user.id) == 1


async def test_expired_trial_cannot_be_reissued(db_session):
    user = await create_user(
        db=db_session,
        email="trial-expired@example.com",
        password=PASSWORD,
        full_name="Expired",
        phone=None,
        company=None,
    )
    subscription = await grant_trial_subscription(db_session, user)

    now = datetime.now(timezone.utc)
    subscription.start_date = now - timedelta(days=40)
    subscription.end_date = now - timedelta(days=10)
    await db_session.flush()

    assert await grant_trial_subscription(db_session, user) is None
    assert await get_active_subscription(db_session, user.id) is None
    assert await _count_subscriptions(db_session, user.id) == 1


async def test_expired_trial_user_loses_product_access(client, db_session):
    user = await create_user(
        db=db_session,
        email="trial-lapsed@example.com",
        password=PASSWORD,
        full_name="Lapsed",
        phone=None,
        company=None,
    )
    subscription = await grant_trial_subscription(db_session, user)
    now = datetime.now(timezone.utc)
    subscription.start_date = now - timedelta(days=40)
    subscription.end_date = now - timedelta(days=10)
    await db_session.flush()

    resp = await client.get("/api/products", headers=_auth(create_access_token(user.id)))

    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"]["code"] == "subscription_required"


async def test_trial_not_granted_when_subscription_already_active(db_session):
    user = User(
        email="trial-haspaid@example.com",
        password_hash=hash_password(PASSWORD),
        full_name="Paid",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(
        Subscription(
            user_id=user.id,
            plan=PlanEnum.advanced,
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True,
        )
    )
    await db_session.flush()

    assert await grant_trial_subscription(db_session, user) is None
    assert user.trial_used is False
    assert await _count_subscriptions(db_session, user.id) == 1


async def test_registering_twice_with_same_email_does_not_duplicate_trial(client, db_session):
    await _register(client, "trial-dup@example.com")

    duplicate = await client.post(
        "/api/auth/register",
        json={
            "email": "trial-dup@example.com",
            "password": PASSWORD,
            "full_name": "Trial User",
        },
    )

    assert duplicate.status_code == 409
    user = await _get_user(db_session, "trial-dup@example.com")
    assert await _count_subscriptions(db_session, user.id) == 1
