import asyncio
import statistics
import time
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.model.user import User
from src.modules.auth.model.verification import VerificationToken
from src.modules.auth.service.auth import verify_password

pytestmark = pytest.mark.integration

PASSWORD = "s3cret-pass"
NEW_PASSWORD = "n3w-s3cret-pass"
VICTIM = "victim@example.com"

REQUEST_URL = "/api/auth/password-reset/request"
CONFIRM_URL = "/api/auth/password-reset/confirm"
CHANGE_URL = "/api/auth/password/change"
REFRESH_URL = "/api/auth/refresh"
ME_URL = "/api/users/me"


class _CapturingMailer:
    backend = "capture"

    def __init__(self, delay: float = 0.0) -> None:
        self.messages: list[dict] = []
        self.delay = delay

    async def send(self, to, subject, text, html=None):
        if self.delay:
            await asyncio.sleep(self.delay)
        self.messages.append({"to": to, "subject": subject, "text": text, "html": html})


@pytest.fixture
def mailbox(monkeypatch):
    from src.modules.auth.service import password_service

    box = _CapturingMailer()
    monkeypatch.setattr(password_service, "get_mailer", lambda: box)
    return box


@pytest.fixture
def slow_mailbox(monkeypatch):
    from src.modules.auth.service import password_service

    box = _CapturingMailer(delay=0.2)
    monkeypatch.setattr(password_service, "get_mailer", lambda: box)
    return box


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _register(client, email: str = VICTIM, password: str = PASSWORD) -> dict:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Victim"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(client, email: str = VICTIM, password: str = PASSWORD) -> dict:
    resp = await client.post("/api/auth/login", json={"identifier": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _token_from(box: _CapturingMailer) -> str:
    from urllib.parse import unquote

    assert box.messages, "письмо не отправлено"
    text = box.messages[-1]["text"]
    raw = text.split("token=", 1)[1].split()[0].strip().rstrip(".,)")
    return unquote(raw)


async def _user_id(db_session, email: str = VICTIM) -> int:
    result = await db_session.execute(select(User).where(User.email == email))
    return result.scalar_one().id


async def test_attack_reset_request_is_not_throttled_mail_bombing(client, mailbox):
    await _register(client)

    attempts = 40
    accepted = 0
    for _ in range(attempts):
        resp = await client.post(REQUEST_URL, json={"email": VICTIM})
        if resp.status_code == 202:
            accepted += 1

    assert len(mailbox.messages) <= 5, (
        f"эндпоинт восстановления не ограничен: {attempts} запросов дали "
        f"{accepted} принятых и {len(mailbox.messages)} писем на чужой адрес"
    )


async def test_attack_reset_request_kills_victim_token_denial_of_recovery(client, mailbox):
    await _register(client)

    await client.post(REQUEST_URL, json={"email": VICTIM})
    victim_token = _token_from(mailbox)

    await client.post(REQUEST_URL, json={"email": VICTIM})

    resp = await client.post(
        CONFIRM_URL, json={"token": victim_token, "new_password": NEW_PASSWORD}
    )
    assert resp.status_code == 200, (
        "атакующий, дёргая /password-reset/request, гасит токен из письма жертвы "
        f"до его использования (ответ {resp.status_code})"
    )


async def test_attack_reset_token_cannot_be_redeemed_twice_concurrently(client, mailbox, db_engine):
    await _register(client)
    await client.post(REQUEST_URL, json={"email": VICTIM})
    token = _token_from(mailbox)

    from src.modules.auth.service import password_service as ps

    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def redeem(new_password: str):
        async with factory() as session:
            try:
                await ps.confirm_password_reset(session, token, new_password)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                return False

    outcomes = await asyncio.gather(
        redeem("attacker-pass"), redeem("legit-pass"), return_exceptions=True
    )
    succeeded = [o for o in outcomes if o is True]

    async with factory() as fresh:
        victim = (await fresh.execute(select(User).where(User.email == VICTIM))).scalar_one()

    assert len(succeeded) == 1, (
        "одноразовый токен сброса обязан погаситься ровно один раз даже при одновременных "
        f"подтверждениях, иначе при нескольких воркерах пароль перезапишут дважды: {outcomes}"
    )
    assert verify_password("attacker-pass", victim.password_hash) != verify_password(
        "legit-pass", victim.password_hash
    ), "в базе должен остаться ровно один из двух паролей, а не смесь состояний"


async def test_attack_host_header_does_not_leak_into_reset_link(client, mailbox):
    await _register(client)
    resp = await client.post(
        REQUEST_URL,
        json={"email": VICTIM},
        headers={"Host": "evil.example.com", "X-Forwarded-Host": "evil.example.com"},
    )
    assert resp.status_code == 202
    message = mailbox.messages[-1]
    assert "evil.example.com" not in message["text"]
    assert "evil.example.com" not in (message["html"] or "")


async def test_attack_access_token_survives_password_reset(client, mailbox, db_engine):
    await _register(client)
    stolen = (await _login(client))["access_token"]

    alive = await client.get(ME_URL, headers=_auth(stolen))
    assert alive.status_code == 200, alive.text

    await client.post(REQUEST_URL, json={"email": VICTIM})
    token = _token_from(mailbox)
    resp = await client.post(CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD})
    assert resp.status_code == 200, resp.text
    assert "сеанс" in resp.json()["detail"].lower()

    after = await client.get(ME_URL, headers=_auth(stolen))
    assert after.status_code == 401, (
        "после сброса пароля украденный access-токен всё ещё работает "
        f"({after.status_code}), хотя ответ обещает «все прежние сеансы завершены»"
    )


async def test_attack_access_token_survives_password_change(client, mailbox):
    await _register(client)
    tokens = await _login(client)
    stolen = tokens["access_token"]

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=_auth(stolen),
    )
    assert resp.status_code == 200, resp.text

    after = await client.get(ME_URL, headers=_auth(stolen))
    assert (
        after.status_code == 401
    ), f"после смены пароля прежний access-токен продолжает работать ({after.status_code})"


async def test_attack_no_notification_mail_on_password_change(client, mailbox):
    await _register(client)
    tokens = await _login(client)

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=_auth(tokens["access_token"]),
    )
    assert resp.status_code == 200, resp.text

    assert mailbox.messages, (
        "смена пароля не рождает письма-уведомления владельцу — "
        "захват аккаунта проходит незаметно (password_changed_message не используется)"
    )


async def test_attack_no_notification_mail_after_reset_confirm(client, mailbox):
    await _register(client)
    await client.post(REQUEST_URL, json={"email": VICTIM})
    token = _token_from(mailbox)
    sent_before = len(mailbox.messages)

    resp = await client.post(CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD})
    assert resp.status_code == 200, resp.text

    assert (
        len(mailbox.messages) > sent_before
    ), "после успешного сброса пароля владельцу не уходит уведомление"


async def test_attack_timing_oracle_when_mail_backend_is_slow(client, slow_mailbox):
    await _register(client)

    async def _measure(email: str) -> float:
        samples = []
        for _ in range(3):
            started = time.perf_counter()
            await client.post(REQUEST_URL, json={"email": email})
            samples.append(time.perf_counter() - started)
        return statistics.median(samples)

    known = await _measure(VICTIM)
    unknown = await _measure("nobody-here@example.com")
    ratio = known / max(unknown, 1e-6)

    assert ratio < 3.0, (
        f"тайминг выдаёт существование аккаунта: {known * 1000:.0f} мс против "
        f"{unknown * 1000:.0f} мс (в {ratio:.1f} раза). Отправка письма выполняется "
        "внутри запроса, поэтому «сопоставимая работа» не компенсирует задержку SMTP"
    )


async def test_attack_password_change_is_not_throttled(client):
    await _register(client)
    tokens = await _login(client)

    rejected = 0
    for _ in range(30):
        resp = await client.post(
            CHANGE_URL,
            json={"current_password": "wrong-guess", "new_password": NEW_PASSWORD},
            headers=_auth(tokens["access_token"]),
        )
        if resp.status_code == 429:
            rejected += 1

    assert rejected > 0, (
        "30 подряд неверных «текущих паролей» на /api/auth/password/change без единого 429: "
        "строгий лимит покрывает только login/register/refresh"
    )


async def test_attack_email_verify_token_cannot_reset_password(client, db_session):
    await _register(client)
    user_id = await _user_id(db_session)

    from src.modules.auth.service.password_service import hash_reset_token

    raw = "cross-purpose-token-value"
    db_session.add(
        VerificationToken(
            user_id=user_id,
            purpose="email_verify",
            token_hash=hash_reset_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
    )
    await db_session.commit()

    resp = await client.post(CONFIRM_URL, json={"token": raw, "new_password": NEW_PASSWORD})
    assert resp.status_code == 400, resp.text


async def test_attack_expired_token_rejected(client, mailbox, db_session):
    await _register(client)
    await client.post(REQUEST_URL, json={"email": VICTIM})
    token = _token_from(mailbox)

    user_id = await _user_id(db_session)
    stored = (
        await db_session.execute(
            select(VerificationToken).where(
                VerificationToken.user_id == user_id,
                VerificationToken.purpose == "password_reset",
            )
        )
    ).scalar_one()
    stored.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    resp = await client.post(CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD})
    assert resp.status_code == 400, resp.text


async def test_attack_cannot_change_other_user_password(client, db_session):
    await _register(client)
    await _register(client, email="other@example.com")
    attacker = await _login(client, email="other@example.com")

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=_auth(attacker["access_token"]),
    )
    assert resp.status_code == 200, resp.text

    victim = (await db_session.execute(select(User).where(User.email == VICTIM))).scalar_one()
    await db_session.refresh(victim)
    assert verify_password(PASSWORD, victim.password_hash)


async def test_attack_raw_token_absent_from_db_and_response(client, mailbox, db_session):
    await _register(client)
    resp = await client.post(REQUEST_URL, json={"email": VICTIM})
    body = resp.text
    token = _token_from(mailbox)

    assert token not in body

    user_id = await _user_id(db_session)
    rows = (
        (
            await db_session.execute(
                select(VerificationToken).where(VerificationToken.user_id == user_id)
            )
        )
        .scalars()
        .all()
    )
    assert rows
    for row in rows:
        assert row.token_hash != token
        assert len(row.token_hash) == 64

    forged = await client.post(
        CONFIRM_URL, json={"token": rows[0].token_hash, "new_password": NEW_PASSWORD}
    )
    assert forged.status_code == 400


async def test_attack_refresh_tokens_really_dead_after_reset(client, mailbox, db_engine):
    await _register(client)
    session_tokens = await _login(client)

    await client.post(REQUEST_URL, json={"email": VICTIM})
    token = _token_from(mailbox)
    resp = await client.post(CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD})
    assert resp.status_code == 200, resp.text

    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as fresh:
        rows = (await fresh.execute(select(RefreshToken))).scalars().all()
        assert rows
        assert all(row.revoked_at is not None for row in rows), "отзыв не долетел до БД"

    replay = await client.post(REFRESH_URL, json={"refresh_token": session_tokens["refresh_token"]})
    assert replay.status_code == 401, replay.text


async def test_login_timing_does_not_reveal_existing_accounts(client):
    import time as _time

    await _register(client)

    async def measure(email: str) -> float:
        started = _time.perf_counter()
        await client.post(
            "/api/auth/login", json={"identifier": email, "password": "definitely-wrong-pass"}
        )
        return _time.perf_counter() - started

    known_samples = [await measure(VICTIM) for _ in range(3)]
    unknown_samples = [await measure("no-such-user-here@example.com") for _ in range(3)]
    known = min(known_samples)
    unknown = min(unknown_samples)
    ratio = max(known, unknown) / max(min(known, unknown), 1e-6)

    assert ratio < 3, (
        "время ответа /auth/login выдаёт существование аккаунта: "
        f"известный {known * 1000:.0f} мс против неизвестного {unknown * 1000:.0f} мс "
        f"(разница в {ratio:.1f} раз) — по секундомеру перебирается список чужих email"
    )


async def test_reuse_detection_also_kills_access_tokens(client):
    await _register(client)
    stolen = (
        await client.post("/api/auth/login", json={"identifier": VICTIM, "password": PASSWORD})
    ).json()

    rotated = await client.post(
        "/api/auth/refresh", json={"refresh_token": stolen["refresh_token"]}
    )
    assert rotated.status_code == 200, rotated.text
    attacker_access = rotated.json()["access_token"]

    replay = await client.post("/api/auth/refresh", json={"refresh_token": stolen["refresh_token"]})
    assert replay.status_code == 401, replay.text

    after = await client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {attacker_access}"}
    )
    assert after.status_code == 401, (
        "детект кражи обязан гасить и access-токен, иначе украденная сессия живёт "
        f"ещё 15 минут после срабатывания защиты: {after.status_code}"
    )
