from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt

from src.config import settings
from src.middleware.subscription_guard import (
    get_active_subscription,
    require_active_subscription,
)
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_access_token, create_refresh_token

pytestmark = pytest.mark.integration


async def _make_user(db, email: str, *, is_active: bool = True, is_admin: bool = False) -> User:
    user = User(
        email=email,
        password_hash="x",
        full_name="Guard User",
        phone=None,
        company=None,
        is_active=is_active,
        is_admin=is_admin,
    )
    db.add(user)
    await db.flush()
    return user


async def _make_subscription(
    db,
    user_id: int,
    *,
    plan: PlanEnum = PlanEnum.basic,
    starts_days_ago: int = 1,
    ends_in_days: int = 30,
    is_active: bool = True,
) -> Subscription:
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user_id,
        plan=plan,
        start_date=now - timedelta(days=starts_days_ago),
        end_date=now + timedelta(days=ends_in_days),
        is_active=is_active,
    )
    db.add(subscription)
    await db.flush()
    return subscription


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_missing_authorization_header_is_rejected_with_403(client):
    resp = await client.get("/api/users/me")

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Not authenticated"


async def test_non_bearer_scheme_is_rejected_with_403(client):
    resp = await client.get("/api/users/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Invalid authentication credentials"


async def test_garbage_bearer_token_returns_401(client):
    resp = await client.get("/api/users/me", headers=_auth("not-a-jwt"))

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid or expired access token"


async def test_token_signed_with_wrong_secret_returns_401(client, db_session):
    user = await _make_user(db_session, "wrongkey@example.com")
    forged = jwt.encode(
        {
            "sub": str(user.id),
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        },
        "definitely-not-the-real-secret",
        algorithm=settings.jwt_algorithm,
    )

    resp = await client.get("/api/users/me", headers=_auth(forged))

    assert resp.status_code == 401


async def test_refresh_token_is_rejected_as_access_token(client, db_session):
    user = await _make_user(db_session, "refresh@example.com")

    resp = await client.get("/api/users/me", headers=_auth(create_refresh_token(user.id)))

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid or expired access token"


async def test_expired_access_token_returns_401(client, db_session):
    user = await _make_user(db_session, "expired@example.com")
    expired = jwt.encode(
        {
            "sub": str(user.id),
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    resp = await client.get("/api/users/me", headers=_auth(expired))

    assert resp.status_code == 401


async def test_access_token_for_unknown_user_returns_401(client):
    resp = await client.get("/api/users/me", headers=_auth(create_access_token(9_999_999)))

    assert resp.status_code == 401
    assert resp.json()["detail"] == "User not found or inactive"


async def test_access_token_for_inactive_user_returns_401(client, db_session):
    user = await _make_user(db_session, "inactive@example.com", is_active=False)

    resp = await client.get("/api/users/me", headers=_auth(create_access_token(user.id)))

    assert resp.status_code == 401
    assert resp.json()["detail"] == "User not found or inactive"


async def test_valid_access_token_returns_current_user(client, db_session):
    user = await _make_user(db_session, "valid@example.com")

    resp = await client.get("/api/users/me", headers=_auth(create_access_token(user.id)))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == user.id
    assert body["email"] == "valid@example.com"
    assert body["full_name"] == "Guard User"
    assert body["is_active"] is True
    assert body["is_admin"] is False


async def test_user_deactivated_after_token_issue_loses_access(client, db_session):
    user = await _make_user(db_session, "revoked@example.com")
    token = create_access_token(user.id)

    first = await client.get("/api/users/me", headers=_auth(token))
    assert first.status_code == 200, first.text

    user.is_active = False
    await db_session.flush()

    second = await client.get("/api/users/me", headers=_auth(token))
    assert second.status_code == 401


async def test_admin_endpoint_forbidden_for_regular_user(client, db_session):
    user = await _make_user(db_session, "regular@example.com", is_admin=False)

    resp = await client.get("/api/admin/stats", headers=_auth(create_access_token(user.id)))

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin access required"


async def test_admin_endpoint_allows_admin_user(client, db_session):
    admin = await _make_user(db_session, "admin@example.com", is_admin=True)

    resp = await client.get("/api/admin/stats", headers=_auth(create_access_token(admin.id)))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total_users"] >= 1
    assert set(body) == {
        "total_users",
        "active_subscriptions",
        "total_products",
        "total_stores",
    }


async def test_inactive_admin_is_rejected_with_401_not_403(client, db_session):
    admin = await _make_user(db_session, "deadadmin@example.com", is_active=False, is_admin=True)

    resp = await client.get("/api/admin/stats", headers=_auth(create_access_token(admin.id)))

    assert resp.status_code == 401


async def test_require_active_subscription_forbids_user_without_subscription(db_session):
    user = await _make_user(db_session, "nosub@example.com")

    with pytest.raises(HTTPException) as exc_info:
        await require_active_subscription(db=db_session, current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "subscription_required"
    assert exc_info.value.detail["message"]


async def test_require_active_subscription_returns_active_subscription(db_session):
    user = await _make_user(db_session, "withsub@example.com")
    subscription = await _make_subscription(db_session, user.id, plan=PlanEnum.advanced)

    result = await require_active_subscription(db=db_session, current_user=user)

    assert result.id == subscription.id
    assert result.plan == PlanEnum.advanced


async def test_require_active_subscription_rejects_expired_subscription(db_session):
    user = await _make_user(db_session, "expiredsub@example.com")
    await _make_subscription(
        db_session,
        user.id,
        starts_days_ago=40,
        ends_in_days=-10,
        is_active=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        await require_active_subscription(db=db_session, current_user=user)

    assert exc_info.value.status_code == 403


async def test_require_active_subscription_rejects_deactivated_subscription(db_session):
    user = await _make_user(db_session, "cancelled@example.com")
    await _make_subscription(db_session, user.id, is_active=False)

    with pytest.raises(HTTPException) as exc_info:
        await require_active_subscription(db=db_session, current_user=user)

    assert exc_info.value.status_code == 403


async def test_get_active_subscription_returns_none_without_subscription(db_session):
    user = await _make_user(db_session, "none@example.com")

    assert await get_active_subscription(db_session, user.id) is None


async def test_get_active_subscription_skips_expired_and_returns_live_one(db_session):
    user = await _make_user(db_session, "mixed@example.com")
    await _make_subscription(
        db_session, user.id, plan=PlanEnum.trial, starts_days_ago=90, ends_in_days=-30
    )
    live = await _make_subscription(db_session, user.id, plan=PlanEnum.advanced)

    result = await get_active_subscription(db_session, user.id)

    assert result is not None
    assert result.id == live.id


async def test_get_active_subscription_is_scoped_to_the_user(db_session):
    owner = await _make_user(db_session, "owner@example.com")
    stranger = await _make_user(db_session, "stranger@example.com")
    await _make_subscription(db_session, owner.id, plan=PlanEnum.advanced)

    assert await get_active_subscription(db_session, stranger.id) is None
