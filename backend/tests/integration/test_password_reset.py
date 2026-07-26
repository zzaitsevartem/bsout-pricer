import hashlib
import logging
import statistics
import time
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from src.config import settings
from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.model.user import User
from src.modules.auth.model.verification import VerificationToken
from src.modules.auth.service.auth import verify_password
from src.modules.auth.service.password_service import (
    PURPOSE_PASSWORD_RESET,
    hash_reset_token,
)

pytestmark = pytest.mark.integration

PASSWORD = "s3cret-pass"
NEW_PASSWORD = "n3w-s3cret-pass"
EMAIL = "reset@example.com"

REQUEST_URL = "/api/auth/password-reset/request"
CONFIRM_URL = "/api/auth/password-reset/confirm"
CHANGE_URL = "/api/auth/password/change"


class _CapturingMailer:
    backend = "capture"

    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send(self, to, subject, text, html=None):
        self.messages.append({"to": to, "subject": subject, "text": text, "html": html})


@pytest.fixture
def mailbox(monkeypatch):
    from src.modules.auth.service import password_service

    box = _CapturingMailer()
    monkeypatch.setattr(password_service, "get_mailer", lambda: box)
    return box


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _register(client, email: str = EMAIL, password: str = PASSWORD) -> dict:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Reset User"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(client, email: str = EMAIL, password: str = PASSWORD) -> dict:
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _token_from_mailbox(mailbox: _CapturingMailer) -> str:
    assert mailbox.messages, "письмо не было отправлено"
    text = mailbox.messages[-1]["text"]
    marker = "token="
    assert marker in text, text
    raw = text.split(marker, 1)[1].split()[0].strip().rstrip(".,)")
    from urllib.parse import unquote

    return unquote(raw)


async def _request_reset(client, email: str = EMAIL):
    return await client.post(REQUEST_URL, json={"email": email})


async def _tokens_in_db(db_session, user_id: int) -> list[VerificationToken]:
    db_session.expire_all()
    result = await db_session.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user_id,
            VerificationToken.purpose == PURPOSE_PASSWORD_RESET,
        )
    )
    return list(result.scalars().all())


async def test_reset_request_returns_202_for_existing_email(client, mailbox):
    await _register(client)

    resp = await _request_reset(client)

    assert resp.status_code == 202, resp.text
    assert len(mailbox.messages) == 1
    assert mailbox.messages[0]["to"] == EMAIL


async def test_reset_request_works_with_the_real_console_mailer(
    client, db_session, caplog, monkeypatch
):
    monkeypatch.setattr(settings, "mail_backend", "console")
    await _register(client)

    with caplog.at_level(logging.INFO, logger="bscout.mail"):
        resp = await _request_reset(client)

    assert resp.status_code == 202, resp.text

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert EMAIL in logged

    db_session.expire_all()
    rows = (
        (
            await db_session.execute(
                select(VerificationToken).where(VerificationToken.purpose == PURPOSE_PASSWORD_RESET)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].token_hash not in logged


async def test_reset_request_matches_email_case_insensitively(client, mailbox):
    await _register(client)

    resp = await _request_reset(client, "ReSeT@ExAmPlE.com")

    assert resp.status_code == 202, resp.text
    assert len(mailbox.messages) == 1
    token = _token_from_mailbox(mailbox)

    confirm = await client.post(CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD})
    assert confirm.status_code == 200, confirm.text


async def test_reset_request_response_is_identical_for_unknown_email(client, mailbox):
    await _register(client)

    known = await _request_reset(client, EMAIL)
    unknown = await _request_reset(client, "nobody@example.com")

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()


async def test_reset_request_sends_no_mail_for_unknown_email(client, mailbox):
    resp = await _request_reset(client, "nobody@example.com")

    assert resp.status_code == 202
    assert mailbox.messages == []


async def test_reset_request_timing_is_comparable_for_unknown_email(client, mailbox):
    await _register(client)

    async def _measure(email: str) -> float:
        started = time.perf_counter()
        await _request_reset(client, email)
        return time.perf_counter() - started

    known = [await _measure(EMAIL) for _ in range(5)]
    unknown = [await _measure("nobody@example.com") for _ in range(5)]

    ratio = statistics.median(known) / max(statistics.median(unknown), 1e-6)
    assert 0.15 < ratio < 6.0, f"timing leak: known={known} unknown={unknown}"


async def test_database_stores_only_the_hash_of_the_token(client, db_session, mailbox):
    body = await _register(client)
    user_id = int(__import__("jose").jwt.get_unverified_claims(body["access_token"])["sub"])

    await _request_reset(client)
    raw_token = _token_from_mailbox(mailbox)

    rows = await _tokens_in_db(db_session, user_id)
    assert len(rows) == 1
    row = rows[0]
    assert row.purpose == PURPOSE_PASSWORD_RESET
    assert row.token_hash != raw_token
    assert row.token_hash == hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    assert row.token_hash == hash_reset_token(raw_token)
    assert len(row.token_hash) == 64
    assert raw_token not in str(row.__dict__)


async def test_reset_token_has_one_hour_ttl(client, db_session, mailbox):
    await _register(client)
    await _request_reset(client)

    rows = await _tokens_in_db(db_session, 1)
    assert rows
    expires_at = rows[0].expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    delta = expires_at - datetime.now(timezone.utc)
    assert timedelta(minutes=50) < delta <= timedelta(hours=1, minutes=1)


async def test_reset_confirm_changes_password_and_allows_login(client, db_session, mailbox):
    await _register(client)
    await _request_reset(client)
    raw_token = _token_from_mailbox(mailbox)

    resp = await client.post(CONFIRM_URL, json={"token": raw_token, "new_password": NEW_PASSWORD})
    assert resp.status_code == 200, resp.text

    old_login = await client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert old_login.status_code == 401

    await _login(client, EMAIL, NEW_PASSWORD)

    db_session.expire_all()
    user = (await db_session.execute(select(User).where(User.email == EMAIL))).scalar_one()
    assert verify_password(NEW_PASSWORD, user.password_hash)


async def test_reset_token_is_single_use(client, mailbox):
    await _register(client)
    await _request_reset(client)
    raw_token = _token_from_mailbox(mailbox)

    first = await client.post(CONFIRM_URL, json={"token": raw_token, "new_password": NEW_PASSWORD})
    assert first.status_code == 200, first.text

    second = await client.post(
        CONFIRM_URL, json={"token": raw_token, "new_password": "another-pass-1"}
    )
    assert second.status_code == 400


async def test_previous_unused_tokens_are_invalidated_by_a_new_request(client, mailbox):
    await _register(client)

    await _request_reset(client)
    stale_token = _token_from_mailbox(mailbox)
    await _request_reset(client)
    fresh_token = _token_from_mailbox(mailbox)

    assert stale_token != fresh_token

    stale = await client.post(
        CONFIRM_URL, json={"token": stale_token, "new_password": NEW_PASSWORD}
    )
    assert stale.status_code == 400

    fresh = await client.post(
        CONFIRM_URL, json={"token": fresh_token, "new_password": NEW_PASSWORD}
    )
    assert fresh.status_code == 200, fresh.text


async def test_expired_reset_token_is_rejected(client, db_session, mailbox):
    await _register(client)
    db_session.expire_all()
    user = (await db_session.execute(select(User).where(User.email == EMAIL))).scalar_one()

    raw_token = "expired-token-value-for-tests"
    db_session.add(
        VerificationToken(
            user_id=user.id,
            purpose=PURPOSE_PASSWORD_RESET,
            token_hash=hash_reset_token(raw_token),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
    )
    await db_session.commit()

    resp = await client.post(CONFIRM_URL, json={"token": raw_token, "new_password": NEW_PASSWORD})

    assert resp.status_code == 400


async def test_unknown_expired_and_used_tokens_share_one_message(client, db_session, mailbox):
    await _register(client)
    db_session.expire_all()
    user = (await db_session.execute(select(User).where(User.email == EMAIL))).scalar_one()

    expired_raw = "expired-token-value"
    used_raw = "used-token-value"
    now = datetime.now(timezone.utc)
    db_session.add(
        VerificationToken(
            user_id=user.id,
            purpose=PURPOSE_PASSWORD_RESET,
            token_hash=hash_reset_token(expired_raw),
            expires_at=now - timedelta(minutes=1),
        )
    )
    db_session.add(
        VerificationToken(
            user_id=user.id,
            purpose=PURPOSE_PASSWORD_RESET,
            token_hash=hash_reset_token(used_raw),
            expires_at=now + timedelta(hours=1),
            used_at=now - timedelta(minutes=5),
        )
    )
    await db_session.commit()

    details = set()
    for raw in ("never-existed-token", expired_raw, used_raw):
        resp = await client.post(CONFIRM_URL, json={"token": raw, "new_password": NEW_PASSWORD})
        assert resp.status_code == 400, resp.text
        details.add(resp.json()["detail"])

    assert len(details) == 1, details


async def test_reset_kills_every_existing_refresh_token(client, db_session, mailbox):
    first = await _register(client)
    second = await _login(client)

    await _request_reset(client)
    raw_token = _token_from_mailbox(mailbox)
    confirm = await client.post(
        CONFIRM_URL, json={"token": raw_token, "new_password": NEW_PASSWORD}
    )
    assert confirm.status_code == 200, confirm.text

    for session in (first, second):
        resp = await client.post(
            "/api/auth/refresh", json={"refresh_token": session["refresh_token"]}
        )
        assert resp.status_code == 401, resp.text

    db_session.expire_all()
    rows = (
        (await db_session.execute(select(RefreshToken).where(RefreshToken.revoked_at.is_(None))))
        .scalars()
        .all()
    )
    assert rows == []


async def test_reset_confirm_rejects_password_over_72_bytes(client, mailbox):
    await _register(client)
    await _request_reset(client)
    raw_token = _token_from_mailbox(mailbox)

    resp = await client.post(
        CONFIRM_URL,
        json={"token": raw_token, "new_password": "п" * 40},
    )

    assert resp.status_code == 422, resp.text


async def test_password_change_requires_authentication(client):
    resp = await client.post(
        CHANGE_URL, json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    )

    assert resp.status_code in (401, 403)


async def test_password_change_without_current_password_is_rejected(client):
    session = await _register(client)

    resp = await client.post(
        CHANGE_URL, json={"new_password": NEW_PASSWORD}, headers=_auth(session["access_token"])
    )

    assert resp.status_code == 422, resp.text


async def test_password_change_with_wrong_current_password_is_rejected(client, db_session):
    session = await _register(client)

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": "not-my-password", "new_password": NEW_PASSWORD},
        headers=_auth(session["access_token"]),
    )

    assert resp.status_code == 400, resp.text

    db_session.expire_all()
    user = (await db_session.execute(select(User).where(User.email == EMAIL))).scalar_one()
    assert verify_password(PASSWORD, user.password_hash)


async def test_password_change_rejects_password_over_72_bytes(client):
    session = await _register(client)

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": PASSWORD, "new_password": "п" * 40},
        headers=_auth(session["access_token"]),
    )

    assert resp.status_code == 422, resp.text


async def test_password_change_kills_other_sessions_but_keeps_the_caller(client):
    caller = await _register(client)
    other = await _login(client)

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=_auth(caller["access_token"]),
    )
    assert resp.status_code == 200, resp.text

    issued = resp.json()
    assert issued["access_token"] and issued["refresh_token"]
    assert issued["refresh_token"] != caller["refresh_token"]

    dead = await client.post("/api/auth/refresh", json={"refresh_token": other["refresh_token"]})
    assert dead.status_code == 401, dead.text

    alive = await client.post("/api/auth/refresh", json={"refresh_token": issued["refresh_token"]})
    assert alive.status_code == 200, alive.text

    me = await client.get("/api/users/me", headers=_auth(issued["access_token"]))
    assert me.status_code == 200, me.text


async def test_password_change_allows_login_with_the_new_password_only(client):
    session = await _register(client)

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=_auth(session["access_token"]),
    )
    assert resp.status_code == 200, resp.text

    old = await client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert old.status_code == 401

    await _login(client, EMAIL, NEW_PASSWORD)


async def test_reset_email_link_is_built_from_frontend_base_url(client, mailbox, monkeypatch):
    monkeypatch.setattr(settings, "frontend_base_url", "https://bscout.ru")
    await _register(client)

    resp = await client.post(
        REQUEST_URL, json={"email": EMAIL}, headers={"Host": "evil.example.com"}
    )
    assert resp.status_code == 202

    text = mailbox.messages[-1]["text"]
    assert "https://bscout.ru/" in text
    assert "evil.example.com" not in text
    assert "evil.example.com" not in (mailbox.messages[-1]["html"] or "")


async def test_reset_request_does_not_leak_the_token_in_the_response(client, mailbox):
    await _register(client)

    resp = await _request_reset(client)
    raw_token = _token_from_mailbox(mailbox)

    assert raw_token not in resp.text
