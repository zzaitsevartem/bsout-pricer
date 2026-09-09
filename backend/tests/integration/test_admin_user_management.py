from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.model.user import Subscription, User
from src.modules.auth.service.auth import create_access_token, hash_password

pytestmark = pytest.mark.integration

USERS_URL = "/api/admin/users"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(db, email: str, *, is_admin: bool = False, is_active: bool = True) -> User:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Management User",
        is_active=is_active,
        is_admin=is_admin,
    )
    db.add(user)
    await db.flush()
    return user


async def _admin_headers(db, email: str = "admin@example.com") -> dict[str, str]:
    admin = await _make_user(db, email, is_admin=True)
    return _auth(create_access_token(admin.id))


async def _user_by_id(db, user_id: int) -> User | None:
    return (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()


async def test_toggle_admin_promotes_and_demotes(db_session, client):
    headers = await _admin_headers(db_session)
    target = await _make_user(db_session, "target@example.com", is_admin=False)

    promote = await client.post(f"{USERS_URL}/{target.id}/toggle-admin", headers=headers)
    assert promote.status_code == 200
    assert promote.json()["is_admin"] is True

    demote = await client.post(f"{USERS_URL}/{target.id}/toggle-admin", headers=headers)
    assert demote.status_code == 200
    assert demote.json()["is_admin"] is False


async def test_toggle_admin_returns_404_for_missing_user(db_session, client):
    headers = await _admin_headers(db_session)

    resp = await client.post(f"{USERS_URL}/999999/toggle-admin", headers=headers)

    assert resp.status_code == 404


async def test_admin_cannot_toggle_own_role(db_session, client):
    admin = await _make_user(db_session, "admin@example.com", is_admin=True)
    headers = _auth(create_access_token(admin.id))

    resp = await client.post(f"{USERS_URL}/{admin.id}/toggle-admin", headers=headers)

    assert resp.status_code == 400
    assert (await _user_by_id(db_session, admin.id)).is_admin is True


async def test_admin_cannot_block_own_account(db_session, client):
    admin = await _make_user(db_session, "admin@example.com", is_admin=True)
    headers = _auth(create_access_token(admin.id))

    resp = await client.post(f"{USERS_URL}/{admin.id}/toggle-active", headers=headers)

    assert resp.status_code == 400
    assert (await _user_by_id(db_session, admin.id)).is_active is True


async def test_delete_user_removes_user_and_cascades_related_rows(db_session, client):
    headers = await _admin_headers(db_session)
    target = await _make_user(db_session, "victim@example.com", is_admin=False)
    now = datetime.now(timezone.utc)
    db_session.add(
        Subscription(
            user_id=target.id,
            plan="trial",
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True,
            auto_renew=False,
        )
    )
    db_session.add(
        RefreshToken(
            jti="some-jti",
            family_id="some-family",
            user_id=target.id,
            expires_at=now + timedelta(days=1),
        )
    )
    await db_session.flush()

    resp = await client.delete(f"{USERS_URL}/{target.id}", headers=headers)

    assert resp.status_code == 204
    assert await _user_by_id(db_session, target.id) is None
    assert (
        await db_session.execute(select(Subscription).where(Subscription.user_id == target.id))
    ).scalar_one_or_none() is None
    assert (
        await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == target.id))
    ).scalar_one_or_none() is None


async def test_delete_user_returns_404_for_missing_user(db_session, client):
    headers = await _admin_headers(db_session)

    resp = await client.delete(f"{USERS_URL}/999999", headers=headers)

    assert resp.status_code == 404


async def test_admin_cannot_delete_own_account(db_session, client):
    admin = await _make_user(db_session, "admin@example.com", is_admin=True)
    headers = _auth(create_access_token(admin.id))

    resp = await client.delete(f"{USERS_URL}/{admin.id}", headers=headers)

    assert resp.status_code == 400
    assert await _user_by_id(db_session, admin.id) is not None


async def test_regular_user_gets_403_on_everything(db_session, client):
    plain = await _make_user(db_session, "plain@example.com", is_admin=False)
    headers = _auth(create_access_token(plain.id))

    promote = await client.post(f"{USERS_URL}/{plain.id}/toggle-admin", headers=headers)
    delete_resp = await client.delete(f"{USERS_URL}/{plain.id}", headers=headers)

    assert promote.status_code == 403
    assert delete_resp.status_code == 403


async def test_anonymous_requests_are_rejected(db_session, client):
    promote = await client.post(f"{USERS_URL}/1/toggle-admin")
    delete_resp = await client.delete(f"{USERS_URL}/1")

    assert promote.status_code == 403
    assert delete_resp.status_code == 403
