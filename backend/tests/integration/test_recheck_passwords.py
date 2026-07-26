import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.model.user import User
from src.modules.auth.model.verification import VerificationToken
from src.modules.auth.schema.password import MIN_PASSWORD_LENGTH
from src.modules.auth.service.auth import verify_password
from src.modules.auth.service.password_service import (
    PURPOSE_PASSWORD_RESET,
    RESET_MAIL_MAX_PER_WINDOW,
    RESET_REQUESTED_DETAIL,
)
from src.modules.mail import PASSWORD_CHANGED_SUBJECT, PASSWORD_RESET_SUBJECT

pytestmark = pytest.mark.integration

PASSWORD = "s3cret-pass"
NEW_PASSWORD = "n3w-s3cret-pass"
VICTIM = "victim@example.com"
UNKNOWN = "nobody-here@example.com"

REQUEST_URL = "/api/auth/password-reset/request"
CONFIRM_URL = "/api/auth/password-reset/confirm"
CHANGE_URL = "/api/auth/password/change"
LOGIN_URL = "/api/auth/login"
REFRESH_URL = "/api/auth/refresh"
ME_URL = "/api/users/me"


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


async def _register(client, email: str = VICTIM, password: str = PASSWORD) -> dict:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Victim"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _reset_token(box: _CapturingMailer) -> str:
    from urllib.parse import unquote

    links = [m for m in box.messages if m["subject"] == PASSWORD_RESET_SUBJECT]
    assert links, "письмо со ссылкой восстановления не отправлено"
    raw = links[-1]["text"].split("token=", 1)[1].split()[0].strip().rstrip(".,)")
    return unquote(raw)


async def _user_id(db_session, email: str = VICTIM) -> int:
    db_session.expire_all()
    result = await db_session.execute(select(User).where(User.email == email))
    return result.scalar_one().id


async def _age_reset_tokens(db_session, user_id: int, seconds: int) -> None:
    await db_session.execute(
        update(VerificationToken)
        .where(
            VerificationToken.user_id == user_id,
            VerificationToken.purpose == PURPOSE_PASSWORD_RESET,
        )
        .values(created_at=datetime.now(timezone.utc) - timedelta(seconds=seconds))
        .execution_options(synchronize_session=False)
    )
    await db_session.commit()


async def test_recheck_throttled_reset_never_reveals_whether_the_account_exists(
    client, db_session, mailbox
):
    await _register(client)
    user_id = await _user_id(db_session)

    unknown = await client.post(REQUEST_URL, json={"email": UNKNOWN})
    fresh = await client.post(REQUEST_URL, json={"email": VICTIM})
    cooled = await client.post(REQUEST_URL, json={"email": VICTIM})

    for _ in range(RESET_MAIL_MAX_PER_WINDOW):
        await _age_reset_tokens(db_session, user_id, seconds=120)
        await client.post(REQUEST_URL, json={"email": VICTIM})
    over_quota = await client.post(REQUEST_URL, json={"email": VICTIM})

    responses = {
        "unknown": unknown,
        "fresh": fresh,
        "cooldown": cooled,
        "over_quota": over_quota,
    }
    for name, resp in responses.items():
        assert resp.status_code == 202, f"{name}: {resp.status_code} {resp.text}"
        assert resp.json()["detail"] == RESET_REQUESTED_DETAIL, name

    bodies = {name: resp.json() for name, resp in responses.items()}
    assert len(set(map(str, bodies.values()))) == 1, bodies


async def test_recheck_mail_quota_really_caps_delivered_letters(client, db_session, mailbox):
    await _register(client)
    user_id = await _user_id(db_session)

    for _ in range(RESET_MAIL_MAX_PER_WINDOW + 3):
        resp = await client.post(REQUEST_URL, json={"email": VICTIM})
        assert resp.status_code == 202, resp.text
        await _age_reset_tokens(db_session, user_id, seconds=120)

    delivered = [m for m in mailbox.messages if m["subject"] == PASSWORD_RESET_SUBJECT]
    assert len(delivered) == RESET_MAIL_MAX_PER_WINDOW, delivered


async def test_recheck_attacker_exhausting_the_quota_delays_victim_recovery(
    client, db_session, mailbox
):
    await _register(client)
    user_id = await _user_id(db_session)

    for _ in range(RESET_MAIL_MAX_PER_WINDOW):
        await client.post(REQUEST_URL, json={"email": VICTIM})
        await _age_reset_tokens(db_session, user_id, seconds=120)

    before = len(mailbox.messages)
    victim = await client.post(REQUEST_URL, json={"email": VICTIM})

    assert victim.status_code == 202, victim.text
    assert len(mailbox.messages) == before


async def test_recheck_reset_token_is_redeemed_once_under_real_http_concurrency(
    client, db_engine, mailbox
):
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from src.database import get_db
    from src.main import app

    await _register(client)
    await client.post(REQUEST_URL, json={"email": VICTIM})
    token = _reset_token(mailbox)

    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _fresh_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _fresh_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as parallel:
        first, second = await asyncio.gather(
            parallel.post(CONFIRM_URL, json={"token": token, "new_password": "aaaa-winner-pass"}),
            parallel.post(CONFIRM_URL, json={"token": token, "new_password": "bbbb-loser-pass"}),
        )

    codes = sorted([first.status_code, second.status_code])
    assert codes == [200, 400], (first.status_code, second.status_code)

    async with factory() as fresh:
        user = (await fresh.execute(select(User).where(User.email == VICTIM))).scalar_one()
    landed = [
        candidate
        for candidate in ("aaaa-winner-pass", "bbbb-loser-pass")
        if verify_password(candidate, user.password_hash)
    ]
    assert len(landed) == 1, landed


async def test_recheck_claim_primitive_serialises_two_contending_transactions(
    client, db_engine, mailbox
):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from src.modules.auth.service import password_service as ps

    await _register(client)
    await client.post(REQUEST_URL, json={"email": VICTIM})
    token = _reset_token(mailbox)

    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _claim() -> bool:
        async with factory() as session:
            try:
                await ps._claim_reset_token(session, token)
            except ps.PasswordResetError:
                await session.rollback()
                return False
            await session.commit()
            return True

    outcomes = await asyncio.gather(_claim(), _claim(), _claim())

    assert sum(1 for ok in outcomes if ok) == 1, outcomes

    async with factory() as fresh:
        rows = (
            (
                await fresh.execute(
                    select(VerificationToken).where(
                        VerificationToken.token_hash == ps.hash_reset_token(token)
                    )
                )
            )
            .scalars()
            .all()
        )
    assert len(rows) == 1
    assert rows[0].used_at is not None


async def test_recheck_reset_confirm_notifies_the_owner_in_addition_to_the_link(client, mailbox):
    await _register(client)
    await client.post(REQUEST_URL, json={"email": VICTIM})
    token = _reset_token(mailbox)

    resp = await client.post(CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD})
    assert resp.status_code == 200, resp.text

    notifications = [m for m in mailbox.messages if m["subject"] == PASSWORD_CHANGED_SUBJECT]
    assert len(notifications) == 1, mailbox.messages
    assert notifications[0]["to"] == VICTIM


async def test_recheck_password_change_notifies_the_owner(client, mailbox):
    session = await _register(client)

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=_auth(session["access_token"]),
    )
    assert resp.status_code == 200, resp.text

    notifications = [m for m in mailbox.messages if m["subject"] == PASSWORD_CHANGED_SUBJECT]
    assert len(notifications) == 1, mailbox.messages
    assert notifications[0]["to"] == VICTIM


async def test_recheck_refresh_tokens_are_really_revoked_after_change(client, db_session, mailbox):
    session = await _register(client)

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=_auth(session["access_token"]),
    )
    assert resp.status_code == 200, resp.text

    db_session.expire_all()
    rows = (await db_session.execute(select(RefreshToken))).scalars().all()
    stale = [row for row in rows if row.revoked_at is None]
    assert len(stale) == 1, stale

    replay = await client.post(REFRESH_URL, json={"refresh_token": session["refresh_token"]})
    assert replay.status_code == 401, replay.text


async def test_recheck_normal_login_still_works_after_reset_paths_joined_strict_bucket(
    client, mailbox
):
    await _register(client)
    await client.post(REQUEST_URL, json={"email": VICTIM})
    token = _reset_token(mailbox)

    confirm = await client.post(CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD})
    assert confirm.status_code == 200, confirm.text

    login = await client.post(LOGIN_URL, json={"email": VICTIM, "password": NEW_PASSWORD})
    assert login.status_code == 200, login.text

    me = await client.get(ME_URL, headers=_auth(login.json()["access_token"]))
    assert me.status_code == 200, me.text


async def test_recheck_password_change_throttling_also_locks_out_login_from_the_same_ip(
    client, mailbox
):
    session = await _register(client)
    header = _auth(session["access_token"])

    codes = []
    for _ in range(12):
        resp = await client.post(
            CHANGE_URL,
            json={"current_password": "definitely-wrong", "new_password": "brand-new-pass"},
            headers=header,
        )
        codes.append(resp.status_code)

    assert 429 in codes, codes

    login = await client.post(LOGIN_URL, json={"email": VICTIM, "password": PASSWORD})
    assert login.status_code == 429, (
        "строгий бакет общий для /password/change и /login: перебор текущего пароля "
        f"выбивает вход с того же IP ({login.status_code})"
    )


async def test_recheck_registration_still_accepts_six_char_password_that_change_rejects(
    client, mailbox
):
    short = "s3cr3t"
    assert len(short) < MIN_PASSWORD_LENGTH

    session = await _register(client, email="shorty@example.com", password=short)

    resp = await client.post(
        CHANGE_URL,
        json={"current_password": short, "new_password": "abcdef7"},
        headers=_auth(session["access_token"]),
    )
    assert resp.status_code == 422, resp.text
