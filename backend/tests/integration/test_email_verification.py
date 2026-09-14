import hashlib
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import APIRouter, Depends
from sqlalchemy import select

from src.main import app
from src.modules.auth.controller import verification_router
from src.modules.auth.model.user import User
from src.modules.auth.model.verification import VerificationToken
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.auth.service.email_verification_service import (
    RESEND_MAX_ATTEMPTS,
    create_verification_token,
    get_verification_mailer,
    hash_verification_token,
    issue_email_verification,
    require_verified_email,
)

pytestmark = pytest.mark.integration

CONFIRM_URL = "/api/auth/email/confirm"
RESEND_URL = "/api/auth/email/resend"
PROBE_URL = "/api/test-probe/subscription"

_paths = {getattr(route, "path", "") for route in app.routes}
if CONFIRM_URL not in _paths:
    app.include_router(verification_router)

if PROBE_URL not in _paths:
    _probe = APIRouter()

    @_probe.post(PROBE_URL)
    async def _probe_subscription(current_user: User = Depends(require_verified_email)):
        return {"user_id": current_user.id}

    app.include_router(_probe)


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_verification_email(self, *, to: str, link: str, expires_at: datetime) -> None:
        self.sent.append({"to": to, "link": link, "expires_at": expires_at})


class BrokenMailer:
    def __init__(self) -> None:
        self.calls = 0

    async def send_verification_email(self, *, to: str, link: str, expires_at: datetime) -> None:
        self.calls += 1
        raise RuntimeError("smtp is down")


@pytest.fixture
def mailer():
    fake = FakeMailer()
    app.dependency_overrides[get_verification_mailer] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_verification_mailer, None)


@pytest_asyncio.fixture(autouse=True)
async def clear_resend_quota():
    from src.modules.auth.service.email_verification_service import RESEND_QUOTA_PREFIX
    from src.modules.cache.service.redis_cache import get_redis

    redis = get_redis()
    keys = [key async for key in redis.scan_iter(match=f"{RESEND_QUOTA_PREFIX}*")]
    if keys:
        await redis.delete(*keys)
    yield


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(db, email: str, *, verified: bool = False, password: str = "s3cret-pass"):
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Verify User",
        is_active=True,
        email_verified_at=datetime.now(timezone.utc) if verified else None,
    )
    db.add(user)
    await db.flush()
    return user, create_access_token(user.id)


async def test_confirm_marks_user_as_verified(client, db_session):
    user, _ = await _make_user(db_session, "confirm@example.com")
    raw, _token = await create_verification_token(db_session, user.id)

    resp = await client.post(CONFIRM_URL, json={"token": raw})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email_verified"] is True
    assert body["email_verified_at"] is not None
    await db_session.refresh(user)
    assert user.email_verified_at is not None


async def test_confirm_is_single_use(client, db_session):
    user, _ = await _make_user(db_session, "once@example.com")
    raw, _token = await create_verification_token(db_session, user.id)

    first = await client.post(CONFIRM_URL, json={"token": raw})
    second = await client.post(CONFIRM_URL, json={"token": raw})

    assert first.status_code == 200, first.text
    assert second.status_code == 400, second.text
    assert second.json()["detail"]["code"] == "invalid_token"


async def test_expired_token_is_rejected(client, db_session):
    user, _ = await _make_user(db_session, "expired@example.com")
    raw, token = await create_verification_token(db_session, user.id)
    token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.flush()

    resp = await client.post(CONFIRM_URL, json={"token": raw})

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "expired_token"
    await db_session.refresh(user)
    assert user.email_verified_at is None


async def test_unknown_token_is_rejected(client, db_session):
    user, _ = await _make_user(db_session, "stranger@example.com")
    await create_verification_token(db_session, user.id)

    resp = await client.post(CONFIRM_URL, json={"token": "not-a-real-token"})

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "invalid_token"
    await db_session.refresh(user)
    assert user.email_verified_at is None


async def test_password_reset_token_is_not_accepted_as_email_verify(client, db_session):
    user, _ = await _make_user(db_session, "reset@example.com")
    raw, token = await create_verification_token(db_session, user.id, purpose="password_reset")

    resp = await client.post(CONFIRM_URL, json={"token": raw})

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "invalid_token"
    await db_session.refresh(user)
    assert user.email_verified_at is None
    await db_session.refresh(token)
    assert token.used_at is None


async def test_token_is_stored_only_as_sha256(db_session):
    user, _ = await _make_user(db_session, "hashed@example.com")
    raw, token = await create_verification_token(db_session, user.id)

    stored = await db_session.execute(
        select(VerificationToken).where(VerificationToken.user_id == user.id)
    )
    row = stored.scalar_one()
    assert row.token_hash != raw
    assert row.token_hash == hashlib.sha256(raw.encode()).hexdigest()
    assert row.token_hash == hash_verification_token(raw)
    assert len(row.token_hash) == 64
    assert token.purpose == "email_verify"


async def test_issued_token_lives_24_hours(db_session):
    user, _ = await _make_user(db_session, "ttl@example.com")
    _raw, token = await create_verification_token(db_session, user.id)

    delta = token.expires_at - datetime.now(timezone.utc)
    assert timedelta(hours=23, minutes=30) < delta <= timedelta(hours=24)


async def test_issue_email_verification_survives_mailer_failure(db_session):
    user, _ = await _make_user(db_session, "broken-mail@example.com")
    broken = BrokenMailer()

    token = await issue_email_verification(db_session, user, mailer=broken)

    assert broken.calls == 1
    assert token is not None
    stored = await db_session.execute(
        select(VerificationToken).where(VerificationToken.user_id == user.id)
    )
    assert stored.scalar_one() is not None


async def test_resend_requires_authentication(client, mailer):
    resp = await client.post(RESEND_URL)
    assert resp.status_code in (401, 403)
    assert mailer.sent == []


async def test_resend_sends_a_working_token(client, db_session, mailer):
    user, access = await _make_user(db_session, "resend@example.com")

    resp = await client.post(RESEND_URL, headers=_auth(access))

    assert resp.status_code == 200, resp.text
    assert resp.json()["sent"] is True
    assert len(mailer.sent) == 1
    assert mailer.sent[0]["to"] == "resend@example.com"

    stored = await db_session.execute(
        select(VerificationToken).where(VerificationToken.user_id == user.id)
    )
    row = stored.scalar_one()
    assert mailer.sent[0]["link"].split("token=")[-1] != row.token_hash
    raw = mailer.sent[0]["link"].split("token=")[-1]
    confirm = await client.post(CONFIRM_URL, json={"token": raw})
    assert confirm.status_code == 200, confirm.text


async def test_resend_reports_a_mail_failure(client, db_session):
    _user, access = await _make_user(db_session, "mailfail@example.com")
    broken = BrokenMailer()
    app.dependency_overrides[get_verification_mailer] = lambda: broken
    try:
        resp = await client.post(RESEND_URL, headers=_auth(access))
    finally:
        app.dependency_overrides.pop(get_verification_mailer, None)

    assert resp.status_code == 502, resp.text
    assert resp.json()["detail"]["code"] == "mail_send_failed"
    assert broken.calls == 1


async def test_resend_conflicts_when_already_verified(client, db_session, mailer):
    _user, access = await _make_user(db_session, "already@example.com", verified=True)

    resp = await client.post(RESEND_URL, headers=_auth(access))

    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "email_already_verified"
    assert mailer.sent == []


async def test_resend_is_rate_limited(client, db_session, mailer):
    _user, access = await _make_user(db_session, "spam@example.com")

    statuses = []
    for _ in range(RESEND_MAX_ATTEMPTS + 1):
        resp = await client.post(RESEND_URL, headers=_auth(access))
        statuses.append(resp.status_code)

    assert statuses[:RESEND_MAX_ATTEMPTS] == [200] * RESEND_MAX_ATTEMPTS
    assert statuses[-1] == 429
    assert len(mailer.sent) == RESEND_MAX_ATTEMPTS


async def test_resend_quota_is_per_user(client, db_session, mailer):
    _first, first_access = await _make_user(db_session, "quota-a@example.com")
    _second, second_access = await _make_user(db_session, "quota-b@example.com")

    for _ in range(RESEND_MAX_ATTEMPTS):
        await client.post(RESEND_URL, headers=_auth(first_access))

    blocked = await client.post(RESEND_URL, headers=_auth(first_access))
    other = await client.post(RESEND_URL, headers=_auth(second_access))

    assert blocked.status_code == 429
    assert other.status_code == 200, other.text


async def test_unverified_user_cannot_take_a_subscription(client, db_session):
    _user, access = await _make_user(db_session, "gated@example.com")

    resp = await client.post(PROBE_URL, headers=_auth(access))

    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"]["code"] == "email_not_verified"


async def test_verified_user_can_take_a_subscription(client, db_session):
    user, access = await _make_user(db_session, "ungated@example.com")
    raw, _token = await create_verification_token(db_session, user.id)
    confirm = await client.post(CONFIRM_URL, json={"token": raw})
    assert confirm.status_code == 200, confirm.text

    resp = await client.post(PROBE_URL, headers=_auth(access))

    assert resp.status_code == 200, resp.text
    assert resp.json()["user_id"] == user.id


async def test_verification_gate_requires_authentication(client):
    resp = await client.post(PROBE_URL)
    assert resp.status_code in (401, 403)
