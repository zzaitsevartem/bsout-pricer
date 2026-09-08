import asyncio
import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.config import settings
from src.main import app
from src.modules.auth.controller import oauth_router, verification_router
from src.modules.auth.model.user import PlanEnum, User
from src.modules.auth.model.verification import UserIdentity, VerificationToken
from src.modules.auth.service import email_verification_service as evs
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.auth.service.oauth_service import (
    VKProfile,
    get_vk_client,
    set_unusable_password,
)

pytestmark = pytest.mark.integration

AUTHORIZE_URL = "/api/auth/vk/authorize"
CALLBACK_URL = "/api/auth/vk/callback"
VK_LINK_URL = "/api/auth/vk/link"
TELEGRAM_LINK_URL = "/api/auth/telegram/link"

TELEGRAM_PREPARE_URL = "/api/auth/telegram/prepare"


async def _tg_nonce(client, token: str) -> str:
    resp = await client.post(TELEGRAM_PREPARE_URL, headers=_auth(token))
    assert resp.status_code == 200, resp.text
    return resp.json()["nonce"]


CONFIRM_URL = "/api/auth/email/confirm"
RESEND_URL = "/api/auth/email/resend"
PAYMENT_SUBSCRIBE_URL = "/api/payment/subscribe"
USERS_SUBSCRIBE_URL = "/api/users/me/subscription"

BOT_TOKEN = "123456:AAF-test-bot-token"

_paths = {getattr(route, "path", "") for route in app.routes}
if AUTHORIZE_URL not in _paths:
    app.include_router(oauth_router)
if CONFIRM_URL not in _paths:
    app.include_router(verification_router)


class FakeVKClient:
    def __init__(self, profile: VKProfile | None = None) -> None:
        self.profile = profile
        self.calls: list[str] = []

    async def exchange_code(self, code: str) -> VKProfile:
        self.calls.append(code)
        if self.profile is None:
            raise AssertionError("VK client must not be called")
        return self.profile


class RecordingMailer:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_verification_email(self, *, to: str, link: str, expires_at) -> None:
        self.sent.append({"to": to, "link": link, "expires_at": expires_at})


@pytest.fixture
def vk_configured(monkeypatch):
    monkeypatch.setattr(settings, "vk_client_id", "51234567")
    monkeypatch.setattr(settings, "vk_client_secret", "vk-secret")
    monkeypatch.setattr(settings, "vk_redirect_uri", "http://localhost:3000/auth/vk/callback")
    return settings


@pytest.fixture
def vk_client():
    holder = FakeVKClient()
    app.dependency_overrides[get_vk_client] = lambda: holder
    yield holder
    app.dependency_overrides.pop(get_vk_client, None)


@pytest.fixture
def telegram_configured(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", BOT_TOKEN)
    monkeypatch.setattr(settings, "telegram_bot_username", "bscout_bot")
    return BOT_TOKEN


@pytest.fixture
def mailer():
    holder = RecordingMailer()
    app.dependency_overrides[evs.get_verification_mailer] = lambda: holder
    yield holder
    app.dependency_overrides.pop(evs.get_verification_mailer, None)


@pytest.fixture(autouse=True)
async def clean_resend_quota():
    yield
    try:
        from src.modules.cache.service.redis_cache import get_redis

        redis = get_redis()
        keys = await redis.keys(f"{evs.RESEND_QUOTA_PREFIX}*")
        if keys:
            await redis.delete(*keys)
    except Exception:
        pass


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(db, email: str, *, verified: bool, password: str | None = "s3cret-pass"):
    user = User(
        email=email,
        password_hash=hash_password(password) if password else set_unusable_password(),
        full_name="Attack Target",
        is_active=True,
        email_verified_at=datetime.now(timezone.utc) if verified else None,
    )
    db.add(user)
    await db.flush()
    return user, create_access_token(user.id)


async def _state(client) -> str:
    resp = await client.get(AUTHORIZE_URL)
    assert resp.status_code == 200, resp.text
    return resp.json()["state"]


def _telegram_payload(bot_token: str, *, tg_id: int = 777, age_seconds: int = 0) -> dict:
    payload = {
        "id": tg_id,
        "first_name": "Ivan",
        "username": "ivan",
        "auth_date": int(time.time()) - age_seconds,
    }
    check = "\n".join(f"{key}={payload[key]}" for key in sorted(payload))
    secret = hashlib.sha256(bot_token.encode()).digest()
    payload["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return payload


async def test_unverified_user_cannot_start_paid_subscription(client, db_session):
    _, token = await _make_user(db_session, "unverified-payer@example.com", verified=False)

    resp = await client.post(
        PAYMENT_SUBSCRIBE_URL,
        json={"plan": PlanEnum.basic.value},
        headers=_auth(token),
    )

    assert resp.status_code == 403, (
        f"unverified email must not be able to buy a subscription, got {resp.status_code}: "
        f"{resp.text}"
    )


async def test_unverified_user_cannot_create_subscription_via_users_endpoint(client, db_session):
    _, token = await _make_user(db_session, "unverified-bypass@example.com", verified=False)

    resp = await client.post(
        USERS_SUBSCRIBE_URL,
        json={"plan": PlanEnum.basic.value},
        headers=_auth(token),
    )

    assert resp.status_code == 403, (
        "POST /api/users/me/subscription is a second subscription path and must honour the same "
        f"email gate, got {resp.status_code}: {resp.text}"
    )


async def test_resend_quota_survives_redis_outage(client, db_session, mailer, monkeypatch):
    _, token = await _make_user(db_session, "flooder@example.com", verified=False)

    def _broken_redis():
        raise RedisConnectionError("redis down")

    monkeypatch.setattr(evs, "get_redis", _broken_redis)

    statuses = []
    for _ in range(evs.RESEND_MAX_ATTEMPTS + 3):
        resp = await client.post(RESEND_URL, headers=_auth(token))
        statuses.append(resp.status_code)

    assert 429 in statuses, (
        "with Redis unavailable the resend quota fails open: "
        f"statuses={statuses}, mails_sent={len(mailer.sent)}"
    )


async def test_vk_link_rejects_state_minted_for_another_session(
    client, db_session, vk_configured, vk_client
):
    _, attacker_token = await _make_user(db_session, "attacker-state@example.com", verified=True)
    _, victim_token = await _make_user(db_session, "victim-state@example.com", verified=True)

    stolen_state = await _state(client)
    vk_client.profile = VKProfile(provider_user_id="900900", email="attacker@vk.com")

    resp = await client.post(
        VK_LINK_URL,
        json={"code": "attacker-code", "state": stolen_state},
        headers=_auth(victim_token),
    )

    assert resp.status_code == 400, (
        "an anonymous /vk/authorize state must not be redeemable on /vk/link for an arbitrary "
        f"account (login-CSRF / forced identity binding), got {resp.status_code}: {resp.text}"
    )
    assert attacker_token


async def test_vk_link_state_reuse_does_not_yield_account_takeover(
    client, db_session, vk_configured, vk_client
):
    victim, victim_token = await _make_user(db_session, "takeover@example.com", verified=True)

    stolen_state = await _state(client)
    vk_client.profile = VKProfile(provider_user_id="666666", email="mallory@vk.com")
    linked = await client.post(
        VK_LINK_URL,
        json={"code": "mallory-code", "state": stolen_state},
        headers=_auth(victim_token),
    )

    login = await client.post(
        CALLBACK_URL,
        json={"code": "mallory-code", "state": await _state(client)},
    )

    if linked.status_code != 200:
        return

    assert login.status_code != 200 or login.json().get("created") is True, (
        "attacker VK identity bound to the victim account via a replayed state now logs the "
        f"attacker in as the victim (user_id={victim.id}): {login.status_code} {login.text}"
    )


async def test_telegram_identity_cannot_be_stolen_by_replaying_a_leaked_payload(
    client, db_session, telegram_configured
):
    _, victim_token = await _make_user(db_session, "tg-owner@example.com", verified=True)
    _, attacker_token = await _make_user(db_session, "tg-thief@example.com", verified=True)

    leaked = _telegram_payload(telegram_configured, tg_id=515151, age_seconds=3600)

    stolen = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _tg_nonce(client, attacker_token)}",
        json=leaked,
        headers=_auth(attacker_token),
    )
    owner = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _tg_nonce(client, victim_token)}",
        json=leaked,
        headers=_auth(victim_token),
    )

    assert not (stolen.status_code == 200 and owner.status_code == 409), (
        "a leaked/observed Telegram widget payload stays valid for 24h and is not bound to the "
        "account that initiated it, so whoever replays it first owns that Telegram id: "
        f"attacker={stolen.status_code} owner={owner.status_code} {owner.text}"
    )


async def test_telegram_payload_cannot_be_replayed_by_a_second_account(
    client, db_session, telegram_configured
):
    _, victim_token = await _make_user(db_session, "tg-victim@example.com", verified=True)
    _, attacker_token = await _make_user(db_session, "tg-attacker@example.com", verified=True)

    payload = _telegram_payload(telegram_configured, tg_id=424242)

    first = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _tg_nonce(client, victim_token)}",
        json=payload,
        headers=_auth(victim_token),
    )
    assert first.status_code == 200, first.text

    replay = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _tg_nonce(client, attacker_token)}",
        json=payload,
        headers=_auth(attacker_token),
    )

    assert replay.status_code in (401, 409), (
        "the very same signed Telegram payload must not be replayable by a different account, "
        f"got {replay.status_code}: {replay.text}"
    )
    assert "telegram_bad_signature" not in replay.text or replay.status_code == 401


async def test_telegram_forged_signature_with_raw_token_key_is_rejected(
    client, db_session, telegram_configured
):
    _, token = await _make_user(db_session, "tg-forge@example.com", verified=True)

    payload = {
        "id": 555,
        "first_name": "Mallory",
        "auth_date": int(time.time()),
    }
    check = "\n".join(f"{key}={payload[key]}" for key in sorted(payload))
    payload["hash"] = hmac.new(
        telegram_configured.encode(), check.encode(), hashlib.sha256
    ).hexdigest()

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _tg_nonce(client, token)}",
        json=payload,
        headers=_auth(token),
    )

    assert resp.status_code == 401, resp.text


async def test_telegram_extra_field_must_be_inside_signature(
    client, db_session, telegram_configured
):
    _, token = await _make_user(db_session, "tg-extra@example.com", verified=True)

    payload = _telegram_payload(telegram_configured, tg_id=606)
    payload["is_premium"] = "true"

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _tg_nonce(client, token)}",
        json=payload,
        headers=_auth(token),
    )

    assert (
        resp.status_code == 401
    ), f"unsigned extra fields must break the check string, got {resp.status_code}: {resp.text}"


async def test_telegram_id_cannot_be_swapped_while_keeping_signature(
    client, db_session, telegram_configured
):
    _, token = await _make_user(db_session, "tg-swap@example.com", verified=True)

    payload = _telegram_payload(telegram_configured, tg_id=111)
    payload["id"] = 222

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _tg_nonce(client, token)}",
        json=payload,
        headers=_auth(token),
    )

    assert resp.status_code == 401, resp.text


async def test_telegram_link_without_bot_token_never_skips_verification(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    _, token = await _make_user(db_session, "tg-unconfigured@example.com", verified=True)

    payload = _telegram_payload(BOT_TOKEN, tg_id=333)
    resp = await client.post(
        TELEGRAM_LINK_URL + "?nonce=any-nonce-value",
        json=payload,
        headers=_auth(token),
    )

    assert resp.status_code == 503, resp.text
    assert resp.json()["detail"]["code"] == "telegram_not_configured"


async def test_telegram_missing_hash_is_rejected(client, db_session, telegram_configured):
    _, token = await _make_user(db_session, "tg-nohash@example.com", verified=True)

    payload = _telegram_payload(telegram_configured, tg_id=444)
    payload.pop("hash")

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _tg_nonce(client, token)}",
        json=payload,
        headers=_auth(token),
    )

    assert resp.status_code in (401, 422), resp.text


async def test_telegram_stale_payload_is_rejected(client, db_session, telegram_configured):
    _, token = await _make_user(db_session, "tg-stale@example.com", verified=True)

    payload = _telegram_payload(telegram_configured, tg_id=888, age_seconds=90000)

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _tg_nonce(client, token)}",
        json=payload,
        headers=_auth(token),
    )

    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "telegram_stale_auth"


async def test_vk_callback_cannot_take_over_account_by_email(
    client, db_session, vk_configured, vk_client
):
    victim, _ = await _make_user(db_session, "vk-victim@example.com", verified=True)
    vk_client.profile = VKProfile(provider_user_id="1010", email="vk-victim@example.com")

    resp = await client.post(CALLBACK_URL, json={"code": "c", "state": await _state(client)})

    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "vk_email_registered"
    identities = (
        (await db_session.execute(select(UserIdentity).where(UserIdentity.user_id == victim.id)))
        .scalars()
        .all()
    )
    assert identities == []


async def test_vk_callback_email_is_case_insensitively_matched(
    client, db_session, vk_configured, vk_client
):
    await _make_user(db_session, "case-victim@example.com", verified=True)
    vk_client.profile = VKProfile(provider_user_id="2020", email="Case-Victim@Example.com")

    resp = await client.post(CALLBACK_URL, json={"code": "c", "state": await _state(client)})

    assert resp.status_code == 409, (
        "case-variant of an existing email must not create a shadow account: "
        f"{resp.status_code} {resp.text}"
    )


async def test_vk_state_is_single_use(client, db_session, vk_configured, vk_client):
    vk_client.profile = VKProfile(provider_user_id="3030", email="fresh-vk@example.com")
    state = await _state(client)

    first = await client.post(CALLBACK_URL, json={"code": "c", "state": state})
    assert first.status_code == 200, first.text

    second = await client.post(CALLBACK_URL, json={"code": "c", "state": state})
    assert second.status_code == 400, second.text
    assert second.json()["detail"]["code"] == "invalid_state"


async def test_vk_callback_without_state_never_calls_provider(
    client, db_session, vk_configured, vk_client
):
    vk_client.profile = None

    resp = await client.post(CALLBACK_URL, json={"code": "c", "state": "not-a-real-state"})

    assert resp.status_code == 400, resp.text
    assert vk_client.calls == []


async def test_vk_created_user_cannot_login_with_any_password(
    client, db_session, vk_configured, vk_client
):
    vk_client.profile = VKProfile(provider_user_id="4040", email="vkonly@example.com")
    created = await client.post(CALLBACK_URL, json={"code": "c", "state": await _state(client)})
    assert created.status_code == 200, created.text

    user = (
        await db_session.execute(select(User).where(User.email == "vkonly@example.com"))
    ).scalar_one()

    for attempt in ["", "x", user.password_hash, "." * 31]:
        resp = await client.post(
            "/api/auth/login", json={"identifier": "vkonly@example.com", "password": attempt}
        )
        assert resp.status_code == 401, f"password={attempt!r} -> {resp.status_code} {resp.text}"


async def test_confirm_token_is_single_use_under_concurrency(db_engine, db_session):
    user, _ = await _make_user(db_session, "race@example.com", verified=False)
    raw, _token = await evs.create_verification_token(db_session, user.id)
    await db_session.commit()

    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _attempt():
        async with factory() as session:
            try:
                await evs.confirm_email(session, raw)
                await session.commit()
                return "ok"
            except evs.EmailVerificationError as exc:
                await session.rollback()
                return exc.code
            except Exception as exc:
                await session.rollback()
                return f"error:{type(exc).__name__}:{exc}"

    results = await asyncio.gather(_attempt(), _attempt())

    assert sorted(results) == ["invalid_token", "ok"], results

    used = (
        (
            await db_session.execute(
                select(VerificationToken).where(VerificationToken.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len([t for t in used if t.used_at is not None]) == 1


async def test_password_reset_token_cannot_confirm_email(client, db_session):
    user, _ = await _make_user(db_session, "cross-purpose@example.com", verified=False)
    raw, _ = await evs.create_verification_token(db_session, user.id, purpose="password_reset")
    await db_session.flush()

    resp = await client.post(CONFIRM_URL, json={"token": raw})

    assert resp.status_code == 400, resp.text
    await db_session.refresh(user)
    assert user.email_verified_at is None


async def test_expired_confirm_token_is_rejected(client, db_session):
    user, _ = await _make_user(db_session, "expired@example.com", verified=False)
    raw, token = await evs.create_verification_token(db_session, user.id)
    token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.flush()

    resp = await client.post(CONFIRM_URL, json={"token": raw})

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "expired_token"
    await db_session.refresh(user)
    assert user.email_verified_at is None


async def test_confirm_token_only_verifies_its_own_owner(client, db_session):
    owner, _ = await _make_user(db_session, "owner@example.com", verified=False)
    bystander, _ = await _make_user(db_session, "bystander@example.com", verified=False)
    raw, _ = await evs.create_verification_token(db_session, owner.id)
    await db_session.flush()

    resp = await client.post(CONFIRM_URL, json={"token": raw})
    assert resp.status_code == 200, resp.text

    await db_session.refresh(owner)
    await db_session.refresh(bystander)
    assert owner.email_verified_at is not None
    assert bystander.email_verified_at is None


async def test_resend_response_and_db_never_expose_the_raw_token(client, db_session, mailer):
    user, token = await _make_user(db_session, "leak@example.com", verified=False)

    resp = await client.post(RESEND_URL, headers=_auth(token))
    assert resp.status_code == 200, resp.text

    assert len(mailer.sent) == 1
    raw = mailer.sent[0]["link"].split("token=")[1]
    assert raw not in resp.text

    stored = (
        (
            await db_session.execute(
                select(VerificationToken).where(VerificationToken.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert stored
    for row in stored:
        assert row.token_hash != raw
        assert len(row.token_hash) == 64


async def test_resend_invalidates_previous_tokens(client, db_session, mailer):
    _, token = await _make_user(db_session, "rotate@example.com", verified=False)

    first = await client.post(RESEND_URL, headers=_auth(token))
    assert first.status_code == 200, first.text
    second = await client.post(RESEND_URL, headers=_auth(token))
    assert second.status_code == 200, second.text

    old_raw = mailer.sent[0]["link"].split("token=")[1]
    resp = await client.post(CONFIRM_URL, json={"token": old_raw})
    assert resp.status_code == 400, resp.text


async def test_resend_quota_is_enforced_per_user(client, db_session, mailer):
    _, token = await _make_user(db_session, "quota@example.com", verified=False)

    statuses = []
    for _ in range(evs.RESEND_MAX_ATTEMPTS + 2):
        resp = await client.post(RESEND_URL, headers=_auth(token))
        statuses.append(resp.status_code)

    assert statuses[: evs.RESEND_MAX_ATTEMPTS] == [200] * evs.RESEND_MAX_ATTEMPTS, statuses
    assert statuses[evs.RESEND_MAX_ATTEMPTS] == 429, statuses
    assert len(mailer.sent) == evs.RESEND_MAX_ATTEMPTS


async def test_configured_smtp_backend_does_not_fall_back_to_logging_tokens(monkeypatch, caplog):
    monkeypatch.setattr(settings, "mail_backend", "smtp")

    sender = evs.get_verification_mailer()

    assert not isinstance(sender, evs.ConsoleVerificationMailer), (
        "mail_backend='smtp' still returns the console mailer, so raw verification links are "
        "written to application logs instead of being emailed"
    )


async def test_raw_token_is_not_logged_when_smtp_backend_is_configured(
    client, db_session, monkeypatch, caplog
):
    import logging

    monkeypatch.setattr(settings, "mail_backend", "smtp")
    caplog.set_level(logging.INFO)

    from src.modules.mail.service.mailer import SmtpMailer

    async def _fake_send(self, to, subject, text, html=None) -> None:  # noqa: ANN001
        return None

    monkeypatch.setattr(SmtpMailer, "send", _fake_send)

    _, token = await _make_user(db_session, "prodlog@example.com", verified=False)

    resp = await client.post(RESEND_URL, headers=_auth(token))
    assert resp.status_code == 200, resp.text

    stored = (
        (
            await db_session.execute(
                select(VerificationToken).where(VerificationToken.used_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    assert stored

    logged = [rec.getMessage() for rec in caplog.records if "[mail:" in rec.getMessage()]
    assert logged == [], (
        "with mail_backend='smtp' the console mailer still writes the single-use verification "
        f"link into the application log: {logged}"
    )


async def test_resend_cannot_target_another_users_address(client, db_session, mailer):
    _, token = await _make_user(db_session, "self@example.com", verified=False)
    await _make_user(db_session, "someone-else@example.com", verified=False)

    resp = await client.post(
        RESEND_URL,
        json={"email": "someone-else@example.com"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    assert [m["to"] for m in mailer.sent] == ["self@example.com"]
