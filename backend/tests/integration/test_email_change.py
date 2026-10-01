from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select

from src.main import app
from src.modules.auth.model.user import User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.auth.service.email_verification_service import (
    EMAIL_CHANGE_FREEZE_PURPOSE,
    EMAIL_CHANGE_NEW_PURPOSE,
    EMAIL_CHANGE_OLD_PURPOSE,
    create_verification_token,
    get_verification_mailer,
)

pytestmark = pytest.mark.integration

CHANGE_URL = "/api/auth/email/change"
CHANGE_OLD_URL = "/api/auth/email/change/confirm/old"
CHANGE_NEW_URL = "/api/auth/email/change/confirm/new"
CHANGE_FREEZE_URL = "/api/auth/email/change/freeze"
CHANGE_CANCEL_URL = "/api/auth/email/change"


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_verification_email(
        self,
        *,
        to: str,
        link: str,
        expires_at: datetime,
        text: str | None = None,
        html: str | None = None,
    ) -> None:
        self.sent.append({"to": to, "link": link, "expires_at": expires_at, "text": text})


@pytest.fixture
def mailer():
    fake = FakeMailer()
    app.dependency_overrides[get_verification_mailer] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_verification_mailer, None)


@pytest_asyncio.fixture(autouse=True)
async def clear_email_change_quota():
    from src.modules.auth.service.email_verification_service import EMAIL_CHANGE_QUOTA_PREFIX
    from src.modules.cache.service.redis_cache import get_redis

    redis = get_redis()
    keys = [key async for key in redis.scan_iter(match=f"{EMAIL_CHANGE_QUOTA_PREFIX}*")]
    if keys:
        await redis.delete(*keys)
    yield


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(db, email: str, *, verified: bool = True, password: str = "s3cret-pass"):
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Change User",
        is_active=True,
        email_verified_at=datetime.now(timezone.utc) if verified else None,
    )
    db.add(user)
    await db.flush()
    return user, create_access_token(user.id)


async def _load_user(db, user_id: int) -> User:
    return (await db.execute(select(User).where(User.id == user_id))).scalar_one()


async def _get_pending_change_token(db, user_id: int, purpose: str) -> str:
    raw, _token = await create_verification_token(db, user_id, purpose=purpose)
    return raw


async def test_request_change_sets_pending_and_mails_old_address_with_freeze(
    client, db_session, mailer
):
    user, token = await _make_user(db_session, "old@example.com")

    resp = await client.post(
        CHANGE_URL, json={"new_email": "new@example.com"}, headers=_auth(token)
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["new_email"] == "new@example.com"
    assert body["sent"] is True

    await db_session.refresh(user)
    assert user.pending_email == "new@example.com"
    assert user.email_change_old_confirmed_at is None

    old_mail = mailer.sent[-1]
    assert old_mail["to"] == "old@example.com"
    assert "purpose=email_change_old" in old_mail["link"]
    assert "я этого не делал" in old_mail["text"].lower()


async def test_full_two_step_change_updates_email(client, db_session, mailer):
    user, token = await _make_user(db_session, "old@example.com")
    await client.post(CHANGE_URL, json={"new_email": "new@example.com"}, headers=_auth(token))
    await db_session.refresh(user)
    assert user.pending_email == "new@example.com"

    old_token = await _get_pending_change_token(db_session, user.id, EMAIL_CHANGE_OLD_PURPOSE)
    resp_old = await client.post(CHANGE_OLD_URL, json={"token": old_token})

    assert resp_old.status_code == 200, resp_old.text
    assert resp_old.json()["status"] == "old_confirmed"
    await db_session.refresh(user)
    assert user.email_change_old_confirmed_at is not None

    new_mail = mailer.sent[-1]
    assert new_mail["to"] == "new@example.com"
    assert "purpose=email_change_new" in new_mail["link"]

    new_token = await _get_pending_change_token(db_session, user.id, EMAIL_CHANGE_NEW_PURPOSE)
    resp_new = await client.post(CHANGE_NEW_URL, json={"token": new_token})

    assert resp_new.status_code == 200, resp_new.text
    assert resp_new.json()["status"] == "new_confirmed"
    await db_session.refresh(user)
    assert user.email == "new@example.com"
    assert user.pending_email is None
    assert user.email_change_old_confirmed_at is None
    assert user.email_verified_at is not None


async def test_confirm_new_without_old_is_rejected(client, db_session):
    user, token = await _make_user(db_session, "old@example.com")
    await client.post(CHANGE_URL, json={"new_email": "new@example.com"}, headers=_auth(token))
    await db_session.refresh(user)

    new_token = await _get_pending_change_token(db_session, user.id, EMAIL_CHANGE_NEW_PURPOSE)
    resp = await client.post(CHANGE_NEW_URL, json={"token": new_token})

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "invalid_token"


async def test_freeze_after_request_deactivates_account(client, db_session):
    user, token = await _make_user(db_session, "old@example.com")
    await client.post(CHANGE_URL, json={"new_email": "new@example.com"}, headers=_auth(token))
    await db_session.refresh(user)
    assert user.pending_email == "new@example.com"

    freeze_token = await _get_pending_change_token(db_session, user.id, EMAIL_CHANGE_FREEZE_PURPOSE)
    resp = await client.post(CHANGE_FREEZE_URL, json={"token": freeze_token})

    assert resp.status_code == 200, resp.text
    assert resp.json()["frozen"] is True
    await db_session.refresh(user)
    assert user.is_active is False
    assert user.pending_email is None
    assert user.email_change_old_confirmed_at is None


async def test_cancel_change_clears_pending(client, db_session):
    user, token = await _make_user(db_session, "old@example.com")
    await client.post(CHANGE_URL, json={"new_email": "new@example.com"}, headers=_auth(token))
    await db_session.refresh(user)
    assert user.pending_email == "new@example.com"

    resp = await client.delete(CHANGE_CANCEL_URL, headers=_auth(token))

    assert resp.status_code == 200, resp.text
    await db_session.refresh(user)
    assert user.pending_email is None


async def test_change_to_taken_email_is_rejected(client, db_session):
    await _make_user(db_session, "taken@example.com")
    user, token = await _make_user(db_session, "old@example.com")

    resp = await client.post(
        CHANGE_URL, json={"new_email": "taken@example.com"}, headers=_auth(token)
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "email_already_taken"


async def test_change_to_same_email_is_rejected(client, db_session):
    user, token = await _make_user(db_session, "old@example.com")

    resp = await client.post(
        CHANGE_URL, json={"new_email": "OLD@example.com"}, headers=_auth(token)
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "email_same"


async def test_duplicate_pending_request_is_rejected(client, db_session):
    user, token = await _make_user(db_session, "old@example.com")
    await client.post(CHANGE_URL, json={"new_email": "new1@example.com"}, headers=_auth(token))
    await db_session.refresh(user)
    assert user.pending_email == "new1@example.com"

    resp = await client.post(
        CHANGE_URL, json={"new_email": "new2@example.com"}, headers=_auth(token)
    )

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "email_change_pending"


async def test_confirm_old_with_unknown_token_is_rejected(client, db_session):
    user, token = await _make_user(db_session, "old@example.com")
    await client.post(CHANGE_URL, json={"new_email": "new@example.com"}, headers=_auth(token))

    resp = await client.post(CHANGE_OLD_URL, json={"token": "not-a-real-token"})

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "invalid_token"


async def test_change_requires_authentication(client, db_session):
    resp = await client.post(CHANGE_URL, json={"new_email": "new@example.com"})

    assert resp.status_code == 401 or resp.status_code == 403


async def test_cancel_without_pending_is_rejected(client, db_session):
    user, token = await _make_user(db_session, "old@example.com")
    await db_session.refresh(user)
    assert user.pending_email is None

    resp = await client.delete(CHANGE_CANCEL_URL, headers=_auth(token))

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "no_pending_email"
