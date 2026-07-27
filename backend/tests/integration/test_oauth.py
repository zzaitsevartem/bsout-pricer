import hashlib
import hmac
import time
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from src.config import settings
from src.main import app
from src.modules.auth.controller import oauth_router
from src.modules.auth.model.user import User
from src.modules.auth.model.verification import UserIdentity
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.auth.service.oauth_service import (
    VKProfile,
    get_vk_client,
    set_unusable_password,
    user_has_usable_password,
)

pytestmark = pytest.mark.integration

AUTHORIZE_URL = "/api/auth/vk/authorize"
CALLBACK_URL = "/api/auth/vk/callback"
VK_LINK_URL = "/api/auth/vk/link"
TELEGRAM_LINK_URL = "/api/auth/telegram/link"
TELEGRAM_PREPARE_URL = "/api/auth/telegram/prepare"
PASSWORD_RESET_REQUEST_URL = "/api/auth/password-reset/request"
PASSWORD_RESET_CONFIRM_URL = "/api/auth/password-reset/confirm"

BOT_TOKEN = "123456:AAF-test-bot-token"

_paths = {getattr(route, "path", "") for route in app.routes}
if AUTHORIZE_URL not in _paths:
    app.include_router(oauth_router)


class FakeVKClient:
    def __init__(self, profile: VKProfile | None = None) -> None:
        self.profile = profile
        self.calls: list[str] = []

    async def exchange_code(self, code: str) -> VKProfile:
        self.calls.append(code)
        if self.profile is None:
            raise AssertionError("VK client must not be called")
        return self.profile


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


def _reset_token_from(mailbox: _CapturingMailer) -> str:
    from urllib.parse import unquote

    assert mailbox.messages, "письмо со ссылкой восстановления не отправлено"
    text = mailbox.messages[-1]["text"]
    raw = text.split("token=", 1)[1].split()[0].strip().rstrip(".,)")
    return unquote(raw)


@pytest.fixture
def telegram_configured(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", BOT_TOKEN)
    monkeypatch.setattr(settings, "telegram_bot_username", "bscout_bot")
    return BOT_TOKEN


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(db, email: str, *, password: str | None = "s3cret-pass"):
    user = User(
        email=email,
        password_hash=hash_password(password) if password else set_unusable_password(),
        full_name="OAuth User",
        is_active=True,
        email_verified_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user, create_access_token(user.id)


async def _state(client, token: str | None = None) -> str:
    url = AUTHORIZE_URL + ("?purpose=link" if token else "")
    headers = _auth(token) if token else {}
    resp = await client.get(url, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["state"]


TELEGRAM_PREPARE_URL = "/api/auth/telegram/prepare"


async def _telegram_nonce(client, access: str) -> str:
    resp = await client.post(TELEGRAM_PREPARE_URL, headers=_auth(access))
    assert resp.status_code == 200, resp.text
    return resp.json()["nonce"]


def _telegram_payload(bot_token: str, *, tg_id: int = 777, age_seconds: int = 0) -> dict:
    payload = {
        "id": tg_id,
        "first_name": "Иван",
        "username": "ivan",
        "auth_date": int(time.time()) - age_seconds,
    }
    check = "\n".join(f"{key}={payload[key]}" for key in sorted(payload))
    secret = hashlib.sha256(bot_token.encode()).digest()
    payload["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return payload


async def test_vk_authorize_returns_url_and_state(client, vk_configured):
    resp = await client.get(AUTHORIZE_URL)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"]
    assert len(body["state"]) >= 20
    assert body["authorize_url"].startswith("https://")
    assert f"state={body['state']}" in body["authorize_url"]
    assert "client_id=51234567" in body["authorize_url"]


async def test_vk_authorize_is_unavailable_without_credentials(client, monkeypatch):
    monkeypatch.setattr(settings, "vk_client_id", None)

    resp = await client.get(AUTHORIZE_URL)

    assert resp.status_code == 503, resp.text
    assert resp.json()["detail"]["code"] == "vk_not_configured"


async def test_vk_states_are_unique(client, vk_configured):
    first = await _state(client)
    second = await _state(client)
    assert first != second


async def test_vk_callback_requires_state(client, vk_configured, vk_client):
    resp = await client.post(CALLBACK_URL, json={"code": "vk-code"})

    assert resp.status_code == 422, resp.text
    assert vk_client.calls == []


async def test_vk_callback_rejects_unknown_state(client, vk_configured, vk_client):
    resp = await client.post(CALLBACK_URL, json={"code": "vk-code", "state": "forged-state"})

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "invalid_state"
    assert vk_client.calls == []


async def test_vk_callback_state_is_single_use(client, db_session, vk_configured, vk_client):
    vk_client.profile = VKProfile(
        provider_user_id="9001", email="fresh@example.com", display_name="Fresh"
    )
    state = await _state(client)

    first = await client.post(CALLBACK_URL, json={"code": "vk-code", "state": state})
    second = await client.post(CALLBACK_URL, json={"code": "vk-code", "state": state})

    assert first.status_code in (200, 201), first.text
    assert second.status_code == 400, second.text
    assert second.json()["detail"]["code"] == "invalid_state"


async def test_vk_callback_creates_account_for_new_email(
    client, db_session, vk_configured, vk_client
):
    vk_client.profile = VKProfile(
        provider_user_id="4242", email="vk-new@example.com", display_name="VK New"
    )
    state = await _state(client)

    resp = await client.post(CALLBACK_URL, json={"code": "vk-code", "state": state})

    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["created"] is True

    user = (
        await db_session.execute(select(User).where(User.email == "vk-new@example.com"))
    ).scalar_one()
    assert user.email_verified_at is not None
    assert user_has_usable_password(user) is False

    identity = (
        await db_session.execute(
            select(UserIdentity).where(
                UserIdentity.provider == "vk", UserIdentity.provider_user_id == "4242"
            )
        )
    ).scalar_one()
    assert identity.user_id == user.id


async def test_vk_callback_does_not_auto_link_existing_email(
    client, db_session, vk_configured, vk_client
):
    existing, _ = await _make_user(db_session, "taken@example.com")
    vk_client.profile = VKProfile(
        provider_user_id="5150", email="taken@example.com", display_name="Impostor"
    )
    state = await _state(client)

    resp = await client.post(CALLBACK_URL, json={"code": "vk-code", "state": state})

    assert resp.status_code == 409, resp.text
    detail = resp.json()["detail"]
    assert detail["code"] == "vk_email_registered"
    assert "access_token" not in resp.json()

    identities = (
        (await db_session.execute(select(UserIdentity).where(UserIdentity.user_id == existing.id)))
        .scalars()
        .all()
    )
    assert identities == []


async def test_vk_callback_requires_email_from_vk(client, db_session, vk_configured, vk_client):
    vk_client.profile = VKProfile(provider_user_id="6060", email=None, display_name="No Mail")
    state = await _state(client)

    resp = await client.post(CALLBACK_URL, json={"code": "vk-code", "state": state})

    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]["code"] == "vk_email_required"
    users = (await db_session.execute(select(User))).scalars().all()
    assert users == []


async def test_vk_callback_reuses_account_for_same_vk_id(
    client, db_session, vk_configured, vk_client
):
    vk_client.profile = VKProfile(
        provider_user_id="7070", email="repeat@example.com", display_name="Repeat"
    )
    first = await client.post(CALLBACK_URL, json={"code": "vk-code", "state": await _state(client)})
    assert first.status_code in (200, 201), first.text

    second = await client.post(
        CALLBACK_URL, json={"code": "vk-code-2", "state": await _state(client)}
    )

    assert second.status_code == 200, second.text
    assert second.json()["created"] is False
    users = (await db_session.execute(select(User))).scalars().all()
    assert len(users) == 1
    identities = (await db_session.execute(select(UserIdentity))).scalars().all()
    assert len(identities) == 1


async def test_vk_callback_ignores_email_change_for_known_vk_id(
    client, db_session, vk_configured, vk_client
):
    vk_client.profile = VKProfile(
        provider_user_id="8080", email="stable@example.com", display_name="Stable"
    )
    await client.post(CALLBACK_URL, json={"code": "c1", "state": await _state(client)})
    victim, _ = await _make_user(db_session, "victim@example.com")

    vk_client.profile = VKProfile(
        provider_user_id="8080", email="victim@example.com", display_name="Stable"
    )
    resp = await client.post(CALLBACK_URL, json={"code": "c2", "state": await _state(client)})

    assert resp.status_code == 200, resp.text
    await db_session.refresh(victim)
    assert victim.email == "victim@example.com"
    identities = (
        (await db_session.execute(select(UserIdentity).where(UserIdentity.user_id == victim.id)))
        .scalars()
        .all()
    )
    assert identities == []


async def test_vk_link_requires_authentication(client, vk_configured, vk_client):
    resp = await client.post(VK_LINK_URL, json={"code": "vk-code", "state": "whatever"})
    assert resp.status_code in (401, 403)
    assert vk_client.calls == []


async def test_vk_link_and_unlink_for_authenticated_user(
    client, db_session, vk_configured, vk_client
):
    user, access = await _make_user(db_session, "linker@example.com")
    vk_client.profile = VKProfile(
        provider_user_id="9090", email="linker@example.com", display_name="Linker"
    )

    linked = await client.post(
        VK_LINK_URL,
        json={"code": "vk-code", "state": await _state(client, access)},
        headers=_auth(access),
    )

    assert linked.status_code in (200, 201), linked.text
    assert linked.json()["provider"] == "vk"
    assert linked.json()["provider_user_id"] == "9090"

    unlinked = await client.request("DELETE", VK_LINK_URL, headers=_auth(access))
    assert unlinked.status_code == 204, unlinked.text
    identities = (
        (await db_session.execute(select(UserIdentity).where(UserIdentity.user_id == user.id)))
        .scalars()
        .all()
    )
    assert identities == []


async def test_vk_link_rejects_identity_owned_by_another_user(
    client, db_session, vk_configured, vk_client
):
    owner, _ = await _make_user(db_session, "owner@example.com")
    db_session.add(
        UserIdentity(user_id=owner.id, provider="vk", provider_user_id="1212", display_name="Own")
    )
    await db_session.flush()
    _thief, thief_access = await _make_user(db_session, "thief@example.com")
    vk_client.profile = VKProfile(
        provider_user_id="1212", email="thief@example.com", display_name="Thief"
    )

    resp = await client.post(
        VK_LINK_URL,
        json={"code": "vk-code", "state": await _state(client, thief_access)},
        headers=_auth(thief_access),
    )

    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "vk_identity_taken"


async def test_vk_unlink_is_blocked_without_a_password(
    client, db_session, vk_configured, vk_client
):
    user, access = await _make_user(db_session, "passwordless@example.com", password=None)
    db_session.add(
        UserIdentity(user_id=user.id, provider="vk", provider_user_id="3131", display_name="Only")
    )
    await db_session.flush()

    resp = await client.request("DELETE", VK_LINK_URL, headers=_auth(access))

    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "last_login_method"
    identities = (
        (await db_session.execute(select(UserIdentity).where(UserIdentity.user_id == user.id)))
        .scalars()
        .all()
    )
    assert len(identities) == 1


async def test_unusable_password_never_authenticates(db_session):
    from src.modules.auth.service.auth import verify_password

    stored = set_unusable_password()
    for candidate in ["", "s3cret-pass", stored, "!"]:
        assert verify_password(candidate, stored) is False


async def test_telegram_link_accepts_a_valid_signature(client, db_session, telegram_configured):
    user, access = await _make_user(db_session, "tg@example.com")
    payload = _telegram_payload(telegram_configured)

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=payload,
        headers=_auth(access),
    )

    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["provider"] == "telegram"
    assert body["provider_user_id"] == "777"
    identity = (
        await db_session.execute(
            select(UserIdentity).where(
                UserIdentity.user_id == user.id, UserIdentity.provider == "telegram"
            )
        )
    ).scalar_one()
    assert identity.display_name == "ivan"


async def test_telegram_link_rejects_a_forged_signature(client, db_session, telegram_configured):
    _user, access = await _make_user(db_session, "forge@example.com")
    payload = _telegram_payload(telegram_configured)
    payload["id"] = 999

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=payload,
        headers=_auth(access),
    )

    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "telegram_bad_signature"
    identities = (await db_session.execute(select(UserIdentity))).scalars().all()
    assert identities == []


async def test_telegram_link_rejects_signature_made_with_raw_token(
    client, db_session, telegram_configured
):
    _user, access = await _make_user(db_session, "rawkey@example.com")
    payload = {"id": 555, "first_name": "Иван", "username": "ivan", "auth_date": int(time.time())}
    check = "\n".join(f"{key}={payload[key]}" for key in sorted(payload))
    payload["hash"] = hmac.new(
        telegram_configured.encode(), check.encode(), hashlib.sha256
    ).hexdigest()

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=payload,
        headers=_auth(access),
    )

    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "telegram_bad_signature"


async def test_telegram_link_rejects_stale_auth_date(client, db_session, telegram_configured):
    _user, access = await _make_user(db_session, "stale@example.com")
    payload = _telegram_payload(telegram_configured, age_seconds=60 * 60 * 25)

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=payload,
        headers=_auth(access),
    )

    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "telegram_stale_auth"


async def test_telegram_link_rejects_future_auth_date(client, db_session, telegram_configured):
    _user, access = await _make_user(db_session, "future@example.com")
    payload = _telegram_payload(telegram_configured, age_seconds=-60 * 60)

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=payload,
        headers=_auth(access),
    )

    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "telegram_stale_auth"


async def test_telegram_link_is_unavailable_without_bot_token(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    _user, access = await _make_user(db_session, "nobot@example.com")
    payload = _telegram_payload(BOT_TOKEN)

    prepare = await client.post(TELEGRAM_PREPARE_URL, headers=_auth(access))
    assert prepare.status_code == 503, prepare.text

    resp = await client.post(
        TELEGRAM_LINK_URL + "?nonce=any-nonce-value",
        json=payload,
        headers=_auth(access),
    )

    assert resp.status_code == 503, resp.text
    assert resp.json()["detail"]["code"] == "telegram_not_configured"


async def test_telegram_link_requires_authentication(client, telegram_configured):
    resp = await client.post(TELEGRAM_LINK_URL, json=_telegram_payload(telegram_configured))
    assert resp.status_code in (401, 403)


async def test_telegram_link_conflicts_when_taken_by_another_user(
    client, db_session, telegram_configured
):
    owner, _ = await _make_user(db_session, "tg-owner@example.com")
    db_session.add(
        UserIdentity(
            user_id=owner.id, provider="telegram", provider_user_id="7771", display_name="owner"
        )
    )
    await db_session.flush()
    _other, other_access = await _make_user(db_session, "tg-other@example.com")

    resp = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, other_access)}",
        json=_telegram_payload(telegram_configured, tg_id=7771),
        headers=_auth(other_access),
    )

    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "telegram_identity_taken"


async def test_telegram_unlink_removes_identity(client, db_session, telegram_configured):
    user, access = await _make_user(db_session, "tg-unlink@example.com")
    await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=_telegram_payload(telegram_configured, tg_id=7772),
        headers=_auth(access),
    )

    resp = await client.request("DELETE", TELEGRAM_LINK_URL, headers=_auth(access))

    assert resp.status_code == 204, resp.text
    identities = (
        (await db_session.execute(select(UserIdentity).where(UserIdentity.user_id == user.id)))
        .scalars()
        .all()
    )
    assert identities == []


async def test_telegram_payload_is_single_use(client, db_session, telegram_configured):
    _user, access = await _make_user(db_session, "tg-once@example.com")
    payload = _telegram_payload(telegram_configured, tg_id=7781)

    first = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=payload,
        headers=_auth(access),
    )
    assert first.status_code in (200, 201), first.text

    await client.request("DELETE", TELEGRAM_LINK_URL, headers=_auth(access))
    replay = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=payload,
        headers=_auth(access),
    )

    assert replay.status_code == 401, replay.text
    assert replay.json()["detail"]["code"] == "telegram_replayed_auth"


async def test_telegram_auth_date_window_is_two_minutes(client, db_session, telegram_configured):
    _user, access = await _make_user(db_session, "tg-window@example.com")

    fresh = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=_telegram_payload(telegram_configured, tg_id=7782, age_seconds=30),
        headers=_auth(access),
    )
    assert fresh.status_code in (200, 201), fresh.text

    await client.request("DELETE", TELEGRAM_LINK_URL, headers=_auth(access))
    stale = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=_telegram_payload(telegram_configured, tg_id=7783, age_seconds=300),
        headers=_auth(access),
    )

    assert stale.status_code == 401, stale.text
    assert stale.json()["detail"]["code"] == "telegram_stale_auth"


async def test_telegram_prepare_issues_a_nonce_bound_to_the_caller(
    client, db_session, telegram_configured
):
    _user, access = await _make_user(db_session, "tg-nonce@example.com")

    resp = await client.post(TELEGRAM_PREPARE_URL, headers=_auth(access))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["nonce"]
    assert body["expires_in"] > 0
    assert body["bot_username"] == "bscout_bot"


async def test_telegram_nonce_of_another_account_is_rejected(
    client, db_session, telegram_configured
):
    _victim, victim_access = await _make_user(db_session, "tg-nonce-owner@example.com")
    _thief, thief_access = await _make_user(db_session, "tg-nonce-thief@example.com")

    prepared = await client.post(TELEGRAM_PREPARE_URL, headers=_auth(victim_access))
    nonce = prepared.json()["nonce"]

    resp = await client.post(
        f"{TELEGRAM_LINK_URL}?nonce={nonce}",
        json=_telegram_payload(telegram_configured, tg_id=7784),
        headers=_auth(thief_access),
    )

    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "telegram_invalid_nonce"
    identities = (await db_session.execute(select(UserIdentity))).scalars().all()
    assert identities == []


async def test_telegram_own_nonce_is_accepted_once(client, db_session, telegram_configured):
    _user, access = await _make_user(db_session, "tg-nonce-ok@example.com")

    prepared = await client.post(TELEGRAM_PREPARE_URL, headers=_auth(access))
    nonce = prepared.json()["nonce"]

    linked = await client.post(
        f"{TELEGRAM_LINK_URL}?nonce={nonce}",
        json=_telegram_payload(telegram_configured, tg_id=7785),
        headers=_auth(access),
    )
    assert linked.status_code in (200, 201), linked.text

    await client.request("DELETE", TELEGRAM_LINK_URL, headers=_auth(access))
    reused = await client.post(
        f"{TELEGRAM_LINK_URL}?nonce={nonce}",
        json=_telegram_payload(telegram_configured, tg_id=7786),
        headers=_auth(access),
    )

    assert reused.status_code == 401, reused.text
    assert reused.json()["detail"]["code"] == "telegram_invalid_nonce"


async def test_vk_only_account_can_set_a_password_and_then_unlink(
    client, db_session, vk_configured, vk_client, mailbox
):
    vk_client.profile = VKProfile(
        provider_user_id="5959", email="vk-locked@example.com", display_name="Locked"
    )
    created = await client.post(
        CALLBACK_URL, json={"code": "vk-code", "state": await _state(client)}
    )
    assert created.status_code in (200, 201), created.text

    blocked = await client.request(
        "DELETE", VK_LINK_URL, headers=_auth(created.json()["access_token"])
    )
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"]["code"] == "last_login_method"

    requested = await client.post(
        PASSWORD_RESET_REQUEST_URL, json={"email": "vk-locked@example.com"}
    )
    assert requested.status_code == 202, requested.text
    raw_token = _reset_token_from(mailbox)

    confirmed = await client.post(
        PASSWORD_RESET_CONFIRM_URL,
        json={"token": raw_token, "new_password": "vk-n3w-pass"},
    )
    assert confirmed.status_code == 200, confirmed.text

    logged_in = await client.post(
        "/api/auth/login", json={"email": "vk-locked@example.com", "password": "vk-n3w-pass"}
    )
    assert logged_in.status_code == 200, logged_in.text

    unlinked = await client.request(
        "DELETE", VK_LINK_URL, headers=_auth(logged_in.json()["access_token"])
    )
    assert unlinked.status_code == 204, unlinked.text
    identities = (await db_session.execute(select(UserIdentity))).scalars().all()
    assert identities == []


async def test_telegram_unlink_is_allowed_without_password(client, db_session, telegram_configured):
    user, access = await _make_user(db_session, "tg-nopass@example.com", password=None)
    linked = await client.post(
        TELEGRAM_LINK_URL + f"?nonce={await _telegram_nonce(client, access)}",
        json=_telegram_payload(telegram_configured, tg_id=7773),
        headers=_auth(access),
    )
    assert linked.status_code in (200, 201), linked.text

    resp = await client.request("DELETE", TELEGRAM_LINK_URL, headers=_auth(access))

    assert resp.status_code == 204, resp.text
