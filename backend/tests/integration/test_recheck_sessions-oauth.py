import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import select

from src.config import settings
from src.main import app
from src.modules.auth.controller import oauth_router, verification_router
from src.modules.auth.model.user import User
from src.modules.auth.model.verification import UserIdentity, VerificationToken
from src.modules.auth.service import email_verification_service as evs
from src.modules.auth.service import oauth_service as oas
from src.modules.auth.service import token_service as ts
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.auth.service.oauth_service import set_unusable_password

pytestmark = pytest.mark.integration

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
LOGOUT_URL = "/api/auth/logout"
ME_URL = "/api/users/me"
CHANGE_URL = "/api/auth/password/change"
RESET_REQUEST_URL = "/api/auth/password-reset/request"
RESET_CONFIRM_URL = "/api/auth/password-reset/confirm"
RESEND_URL = "/api/auth/email/resend"
TELEGRAM_LINK_URL = "/api/auth/telegram/link"
TELEGRAM_PREPARE_URL = "/api/auth/telegram/prepare"
AUTHORIZE_URL = "/api/auth/vk/authorize"

PASSWORD = "s3cret-pass"
NEW_PASSWORD = "n3w-s3cret-pass"
BOT_TOKEN = "123456:AAF-test-bot-token"

_paths = {getattr(route, "path", "") for route in app.routes}
if AUTHORIZE_URL not in _paths:
    app.include_router(oauth_router)
if RESEND_URL not in _paths:
    app.include_router(verification_router)


class _CapturingMailer:
    backend = "capture"

    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send(self, to, subject, text, html=None):
        self.messages.append({"to": to, "subject": subject, "text": text, "html": html})


class _RecordingVerificationMailer:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_verification_email(self, *, to: str, link: str, expires_at) -> None:
        self.sent.append({"to": to, "link": link})


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mailbox(monkeypatch):
    from src.modules.auth.service import password_service

    box = _CapturingMailer()
    monkeypatch.setattr(password_service, "get_mailer", lambda: box)
    return box


@pytest.fixture
def verification_mailer():
    holder = _RecordingVerificationMailer()
    app.dependency_overrides[evs.get_verification_mailer] = lambda: holder
    yield holder
    app.dependency_overrides.pop(evs.get_verification_mailer, None)


@pytest.fixture
def telegram_configured(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", BOT_TOKEN)
    monkeypatch.setattr(settings, "telegram_bot_username", "bscout_bot")
    return BOT_TOKEN


@pytest.fixture(autouse=True)
async def clean_recheck_redis_keys():
    yield
    try:
        from src.modules.cache.service.redis_cache import get_redis

        redis = get_redis()
        for prefix in (
            evs.RESEND_QUOTA_PREFIX,
            oas.TELEGRAM_USED_PREFIX,
            oas.TELEGRAM_NONCE_PREFIX,
            ts.ACCESS_DENYLIST_PREFIX,
        ):
            keys = await redis.keys(f"{prefix}*")
            if keys:
                await redis.delete(*keys)
    except Exception:
        pass


async def _register(client, email: str, password: str = PASSWORD) -> dict:
    resp = await client.post(
        REGISTER_URL, json={"email": email, "password": password, "full_name": "Recheck"}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(client, email: str, password: str = PASSWORD) -> dict:
    resp = await client.post(LOGIN_URL, json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _reset_token_from(box: _CapturingMailer) -> str:
    from urllib.parse import unquote

    assert box.messages, "письмо не отправлено"
    text = box.messages[-1]["text"]
    raw = text.split("token=", 1)[1].split()[0].strip().rstrip(".,)")
    return unquote(raw)


async def _make_user(db, email: str, *, verified: bool = True, password: str | None = PASSWORD):
    user = User(
        email=email,
        password_hash=hash_password(password) if password else set_unusable_password(),
        full_name="Recheck",
        is_active=True,
        email_verified_at=datetime.now(timezone.utc) if verified else None,
    )
    db.add(user)
    await db.flush()
    return user, create_access_token(user.id)


def _telegram_payload(bot_token: str, *, tg_id: int, age_seconds: int = 0) -> dict:
    payload = {
        "id": tg_id,
        "first_name": "Ivan",
        "username": f"ivan{tg_id}",
        "auth_date": int(time.time()) - age_seconds,
    }
    check = "\n".join(f"{key}={payload[key]}" for key in sorted(payload))
    secret = hashlib.sha256(bot_token.encode()).digest()
    payload["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return payload


def _broken_redis_factory():
    def _raise():
        raise RedisConnectionError("redis down")

    return _raise


async def test_recheck_every_parallel_session_dies_after_password_reset(client, mailbox):
    await _register(client, "multi@example.com")
    first = (await _login(client, "multi@example.com"))["access_token"]
    second = (await _login(client, "multi@example.com"))["access_token"]

    assert (await client.get(ME_URL, headers=_auth(first))).status_code == 200
    assert (await client.get(ME_URL, headers=_auth(second))).status_code == 200

    await client.post(RESET_REQUEST_URL, json={"email": "multi@example.com"})
    raw = _reset_token_from(mailbox)
    confirm = await client.post(
        RESET_CONFIRM_URL, json={"token": raw, "new_password": NEW_PASSWORD}
    )
    assert confirm.status_code == 200, confirm.text

    for stolen in (first, second):
        after = await client.get(ME_URL, headers=_auth(stolen))
        assert after.status_code == 401, after.text
        assert "revoked" in after.json()["detail"].lower(), after.text


async def test_recheck_password_reset_does_not_kill_other_users_sessions(client, mailbox):
    await _register(client, "owner@example.com")
    await _register(client, "bystander@example.com")
    bystander = (await _login(client, "bystander@example.com"))["access_token"]

    await client.post(RESET_REQUEST_URL, json={"email": "owner@example.com"})
    raw = _reset_token_from(mailbox)
    confirm = await client.post(
        RESET_CONFIRM_URL, json={"token": raw, "new_password": NEW_PASSWORD}
    )
    assert confirm.status_code == 200, confirm.text

    alive = await client.get(ME_URL, headers=_auth(bystander))
    assert alive.status_code == 200, alive.text


async def test_recheck_token_returned_by_password_change_is_immediately_usable(client, mailbox):
    await _register(client, "changer@example.com")
    old = (await _login(client, "changer@example.com"))["access_token"]

    changed = await client.post(
        CHANGE_URL,
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=_auth(old),
    )
    assert changed.status_code == 200, changed.text
    fresh = changed.json()["access_token"]

    assert (await client.get(ME_URL, headers=_auth(old))).status_code == 401
    still_ok = await client.get(ME_URL, headers=_auth(fresh))
    assert still_ok.status_code == 200, still_ok.text


async def test_recheck_login_right_after_reset_is_not_blocked_by_the_denylist(client, mailbox):
    await _register(client, "relogin@example.com")
    await client.post(RESET_REQUEST_URL, json={"email": "relogin@example.com"})
    raw = _reset_token_from(mailbox)
    assert (
        await client.post(RESET_CONFIRM_URL, json={"token": raw, "new_password": NEW_PASSWORD})
    ).status_code == 200

    fresh = (await _login(client, "relogin@example.com", NEW_PASSWORD))["access_token"]
    resp = await client.get(ME_URL, headers=_auth(fresh))
    assert resp.status_code == 200, resp.text


async def test_recheck_refreshed_access_token_still_works_for_untouched_user(client):
    await _register(client, "refresher@example.com")
    tokens = await _login(client, "refresher@example.com")

    refreshed = await client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refreshed.status_code == 200, refreshed.text
    resp = await client.get(ME_URL, headers=_auth(refreshed.json()["access_token"]))
    assert resp.status_code == 200, resp.text


async def test_recheck_logout_leaves_the_access_token_alive(client):
    await _register(client, "logout@example.com")
    tokens = await _login(client, "logout@example.com")

    out = await client.post(
        LOGOUT_URL,
        json={"refresh_token": tokens["refresh_token"]},
        headers=_auth(tokens["access_token"]),
    )
    assert out.status_code == 204, out.text

    after = await client.get(ME_URL, headers=_auth(tokens["access_token"]))
    assert after.status_code == 200, (
        "если это стало 401 — контракт логаута изменился, обнови отчёт: "
        f"{after.status_code} {after.text}"
    )


async def test_recheck_denylist_is_fail_open_when_redis_is_down(client, mailbox, monkeypatch):
    await _register(client, "failopen@example.com")
    stolen = (await _login(client, "failopen@example.com"))["access_token"]

    await client.post(RESET_REQUEST_URL, json={"email": "failopen@example.com"})
    raw = _reset_token_from(mailbox)
    assert (
        await client.post(RESET_CONFIRM_URL, json={"token": raw, "new_password": NEW_PASSWORD})
    ).status_code == 200
    assert (await client.get(ME_URL, headers=_auth(stolen))).status_code == 401

    monkeypatch.setattr(ts, "get_redis", _broken_redis_factory())
    revived = await client.get(ME_URL, headers=_auth(stolen))
    assert revived.status_code == 200, (
        "denylist перестал быть fail-open — это улучшение, обнови отчёт: "
        f"{revived.status_code} {revived.text}"
    )


async def test_recheck_token_without_iat_is_rejected_after_revocation(client, db_session):
    from datetime import timedelta

    from jose import jwt

    user, _ = await _make_user(db_session, "noiat@example.com")
    legacy = jwt.encode(
        {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "type": "access",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert (await client.get(ME_URL, headers=_auth(legacy))).status_code == 200

    await ts.invalidate_access_tokens(user.id)
    after = await client.get(ME_URL, headers=_auth(legacy))
    assert after.status_code == 401, after.text


async def test_recheck_denylist_marker_is_scoped_to_one_user(db_session):
    user_a, _ = await _make_user(db_session, "scope-a@example.com")
    user_b, _ = await _make_user(db_session, "scope-b@example.com")

    await ts.invalidate_access_tokens(user_a.id)

    assert await ts.access_tokens_invalid_before(user_a.id) is not None
    assert await ts.access_tokens_invalid_before(user_b.id) is None


async def test_recheck_same_user_cannot_replay_its_own_telegram_payload(
    client, db_session, telegram_configured
):
    user, token = await _make_user(db_session, "tg-self@example.com")
    payload = _telegram_payload(telegram_configured, tg_id=9110001)

    first = await client.post(TELEGRAM_LINK_URL, json=payload, headers=_auth(token))
    assert first.status_code == 200, first.text

    second = await client.post(TELEGRAM_LINK_URL, json=payload, headers=_auth(token))
    assert second.status_code == 401, second.text
    assert oas.TELEGRAM_REPLAYED_CODE in second.text


async def test_recheck_telegram_payload_outside_the_window_is_rejected(
    client, db_session, telegram_configured
):
    _, token = await _make_user(db_session, "tg-old@example.com")
    stale = _telegram_payload(telegram_configured, tg_id=9110002, age_seconds=600)

    resp = await client.post(TELEGRAM_LINK_URL, json=stale, headers=_auth(token))
    assert resp.status_code == 401, resp.text
    assert oas.TELEGRAM_STALE_AUTH_CODE in resp.text

    identities = (await db_session.execute(select(UserIdentity))).scalars().all()
    assert identities == []


async def test_recheck_leaked_payload_cannot_be_hijacked_within_the_window(
    client, db_session, telegram_configured
):
    _, victim = await _make_user(db_session, "tg-v@example.com")
    _, thief = await _make_user(db_session, "tg-t@example.com")
    payload = _telegram_payload(telegram_configured, tg_id=9110003, age_seconds=100)

    stolen = await client.post(TELEGRAM_LINK_URL, json=payload, headers=_auth(thief))
    owner = await client.post(TELEGRAM_LINK_URL, json=payload, headers=_auth(victim))
    assert not (stolen.status_code == 200 and owner.status_code != 200), (
        "payload не привязан к аккаунту, который начал привязку: внутри окна "
        f"{oas.TELEGRAM_AUTH_MAX_AGE_SECONDS + oas.TELEGRAM_CLOCK_SKEW_SECONDS} c telegram-id "
        f"забирает тот, кто успел первым (nonce необязателен): "
        f"thief={stolen.status_code} owner={owner.status_code} {owner.text}"
    )


async def test_recheck_nonce_is_not_required_so_the_binding_can_be_skipped(
    client, db_session, telegram_configured
):
    _, owner = await _make_user(db_session, "bind-owner@example.com")
    _, thief = await _make_user(db_session, "bind-thief@example.com")

    prepared = await client.post(TELEGRAM_PREPARE_URL, headers=_auth(owner))
    assert prepared.status_code == 200, prepared.text

    payload = _telegram_payload(telegram_configured, tg_id=9110009)
    bypass = await client.post(TELEGRAM_LINK_URL, json=payload, headers=_auth(thief))
    assert bypass.status_code != 200, (
        "выданный владельцу nonce ничего не защищает: запрос без ?nonce= проходит, "
        f"и telegram-id уходит другому аккаунту ({bypass.status_code})"
    )


async def test_recheck_telegram_link_still_works_without_any_nonce(
    client, db_session, telegram_configured
):
    _, token = await _make_user(db_session, "tg-nononce@example.com")
    payload = _telegram_payload(telegram_configured, tg_id=9110004)

    resp = await client.post(TELEGRAM_LINK_URL, json=payload, headers=_auth(token))
    assert resp.status_code == 200, (
        "nonce стал обязательным — это ужесточение, обнови отчёт: " f"{resp.status_code}"
    )


async def test_recheck_nonce_of_another_user_is_rejected(client, db_session, telegram_configured):
    _, owner = await _make_user(db_session, "nonce-owner@example.com")
    _, other = await _make_user(db_session, "nonce-other@example.com")

    prepared = await client.post(TELEGRAM_PREPARE_URL, headers=_auth(owner))
    assert prepared.status_code == 200, prepared.text
    nonce = prepared.json()["nonce"]

    payload = _telegram_payload(telegram_configured, tg_id=9110005)
    resp = await client.post(
        f"{TELEGRAM_LINK_URL}?nonce={nonce}", json=payload, headers=_auth(other)
    )
    assert resp.status_code == 401, resp.text
    assert oas.TELEGRAM_INVALID_NONCE_CODE in resp.text

    identities = (await db_session.execute(select(UserIdentity))).scalars().all()
    assert identities == []


async def test_recheck_prepare_requires_authentication(client, telegram_configured):
    resp = await client.post(TELEGRAM_PREPARE_URL)
    assert resp.status_code in (401, 403), resp.text


async def test_recheck_telegram_link_is_fail_closed_when_redis_is_down(
    client, db_session, telegram_configured, monkeypatch
):
    _, token = await _make_user(db_session, "tg-redis@example.com")
    payload = _telegram_payload(telegram_configured, tg_id=9110006)
    monkeypatch.setattr(oas, "get_redis", _broken_redis_factory())

    resp = await client.post(TELEGRAM_LINK_URL, json=payload, headers=_auth(token))
    assert resp.status_code == 503, resp.text

    identities = (await db_session.execute(select(UserIdentity))).scalars().all()
    assert identities == []


async def test_recheck_failed_link_burns_the_payload_and_locks_out_the_owner(
    client, db_session, telegram_configured
):
    _, token = await _make_user(db_session, "tg-burn@example.com")
    first = _telegram_payload(telegram_configured, tg_id=9110007)
    assert (
        await client.post(TELEGRAM_LINK_URL, json=first, headers=_auth(token))
    ).status_code == 200

    second = _telegram_payload(telegram_configured, tg_id=9110008)
    conflict = await client.post(TELEGRAM_LINK_URL, json=second, headers=_auth(token))
    assert conflict.status_code == 409, conflict.text

    unlink = await client.delete(TELEGRAM_LINK_URL, headers=_auth(token))
    assert unlink.status_code == 204, unlink.text

    retry = await client.post(TELEGRAM_LINK_URL, json=second, headers=_auth(token))
    assert retry.status_code == 401 and oas.TELEGRAM_REPLAYED_CODE in retry.text, (
        "если это стало 200 — одноразовость перенесена после успешной привязки, обнови отчёт: "
        f"{retry.status_code} {retry.text}"
    )


async def test_recheck_resend_quota_cannot_be_drained_by_another_user(
    client, db_session, verification_mailer
):
    _, victim = await _make_user(db_session, "quota-victim@example.com", verified=False)
    _, noisy = await _make_user(db_session, "quota-noisy@example.com", verified=False)

    for _ in range(evs.RESEND_MAX_ATTEMPTS + 2):
        await client.post(RESEND_URL, headers=_auth(noisy))

    resp = await client.post(RESEND_URL, headers=_auth(victim))
    assert resp.status_code == 200, resp.text


async def test_recheck_resend_is_closed_to_anonymous_callers(client, db_session):
    await _make_user(db_session, "anon-target@example.com", verified=False)

    resp = await client.post(RESEND_URL, json={"email": "anon-target@example.com"})
    assert resp.status_code in (401, 403), resp.text

    missing = await client.post(RESEND_URL, json={"email": "nobody@example.com"})
    assert missing.status_code == resp.status_code
    assert missing.text == resp.text


async def test_recheck_resend_is_fail_closed_while_redis_is_down(
    client, db_session, verification_mailer, monkeypatch
):
    _, token = await _make_user(db_session, "resend-closed@example.com", verified=False)
    monkeypatch.setattr(evs, "get_redis", _broken_redis_factory())

    resp = await client.post(RESEND_URL, headers=_auth(token))
    assert resp.status_code == 429, resp.text
    assert verification_mailer.sent == []


async def test_recheck_resend_recovers_once_redis_is_back(
    client, db_session, verification_mailer, monkeypatch
):
    _, token = await _make_user(db_session, "resend-back@example.com", verified=False)

    monkeypatch.setattr(evs, "get_redis", _broken_redis_factory())
    assert (await client.post(RESEND_URL, headers=_auth(token))).status_code == 429

    monkeypatch.undo()
    resp = await client.post(RESEND_URL, headers=_auth(token))
    assert resp.status_code == 200, resp.text
    assert verification_mailer.sent


async def test_recheck_registration_issues_a_verification_token_without_logging_it(
    client, db_session, caplog
):
    caplog.set_level(logging.DEBUG)
    await _register(client, "regmail@example.com")

    db_session.expire_all()
    rows = (
        (
            await db_session.execute(
                select(VerificationToken).where(
                    VerificationToken.purpose == evs.EMAIL_VERIFY_PURPOSE
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1

    logged = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "/verify-email?token=" not in logged
    assert rows[0].token_hash not in logged


async def test_recheck_console_backend_never_writes_the_verification_link_to_logs(
    client, db_session, monkeypatch, caplog
):
    monkeypatch.setattr(settings, "mail_backend", "console")
    caplog.set_level(logging.DEBUG)
    _, token = await _make_user(db_session, "consolelog@example.com", verified=False)

    resp = await client.post(RESEND_URL, headers=_auth(token))
    assert resp.status_code == 200, resp.text

    logged = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "/verify-email?token=" not in logged, logged


async def test_recheck_misconfigured_smtp_reports_success_while_nothing_is_sent(
    client, db_session, monkeypatch, caplog
):
    monkeypatch.setattr(settings, "mail_backend", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "")
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")
    caplog.set_level(logging.DEBUG)
    _, token = await _make_user(db_session, "smtpbroken@example.com", verified=False)

    resp = await client.post(RESEND_URL, headers=_auth(token))
    assert resp.status_code == 200 and resp.json()["sent"] is True, (
        "если это перестало быть 200 — тихий сбой отправки починен, обнови отчёт: "
        f"{resp.status_code} {resp.text}"
    )

    logged = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "/verify-email?token=" not in logged, logged


async def test_recheck_vk_only_user_is_not_locked_out_of_password_recovery(
    client, db_session, mailbox
):
    user, _ = await _make_user(db_session, "vkonly@example.com", password=None)
    db_session.add(UserIdentity(user_id=user.id, provider="vk", provider_user_id="90001"))
    await db_session.flush()

    assert (
        await client.post(RESET_REQUEST_URL, json={"email": "vkonly@example.com"})
    ).status_code == 202
    raw = _reset_token_from(mailbox)
    assert (
        await client.post(RESET_CONFIRM_URL, json={"token": raw, "new_password": NEW_PASSWORD})
    ).status_code == 200

    logged_in = await client.post(
        LOGIN_URL, json={"email": "vkonly@example.com", "password": NEW_PASSWORD}
    )
    assert logged_in.status_code == 200, logged_in.text
