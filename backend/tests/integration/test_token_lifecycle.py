from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.model.user import User
from src.modules.auth.service.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
)
from src.modules.auth.service.token_service import (
    REASON_LOGOUT,
    REASON_REUSE,
    REASON_ROTATED,
)

pytestmark = pytest.mark.integration

PASSWORD = "s3cret-pass"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _register(client, email: str = "token@example.com") -> dict:
    resp = await client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Token User"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _refresh(client, refresh_token: str):
    return await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})


async def _stored(db_session, jti: str) -> RefreshToken:
    db_session.expire_all()
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    return result.scalar_one()


def _jti(token: str) -> str:
    payload = decode_token(token)
    assert payload is not None
    return payload["jti"]


async def test_register_persists_refresh_token_row(client, db_session):
    body = await _register(client, "persist-token@example.com")

    payload = decode_token(body["refresh_token"])
    assert payload["type"] == "refresh"
    assert payload["jti"]
    assert payload["family_id"] == payload["jti"]

    stored = await _stored(db_session, payload["jti"])
    assert stored.family_id == payload["family_id"]
    assert stored.revoked_at is None
    assert stored.replaced_by_jti is None
    assert stored.expires_at is not None


async def test_login_starts_a_new_token_family(client, db_session):
    registered = await _register(client, "family-start@example.com")
    login = await client.post(
        "/api/auth/login",
        json={"email": "family-start@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200, login.text

    first = decode_token(registered["refresh_token"])
    second = decode_token(login.json()["refresh_token"])
    assert first["family_id"] != second["family_id"]


async def test_refresh_rotates_pair_and_marks_old_token(client, db_session):
    body = await _register(client, "rotate@example.com")
    old_jti = _jti(body["refresh_token"])

    resp = await _refresh(client, body["refresh_token"])
    assert resp.status_code == 200, resp.text
    rotated = resp.json()

    assert rotated["refresh_token"] != body["refresh_token"]
    assert decode_token(rotated["access_token"])["type"] == "access"

    new_payload = decode_token(rotated["refresh_token"])
    assert new_payload["family_id"] == decode_token(body["refresh_token"])["family_id"]

    old = await _stored(db_session, old_jti)
    assert old.revoked_at is not None
    assert old.revoked_reason == REASON_ROTATED
    assert old.replaced_by_jti == new_payload["jti"]

    new = await _stored(db_session, new_payload["jti"])
    assert new.revoked_at is None


async def test_rotated_token_cannot_be_used_again(client):
    body = await _register(client, "rotate-twice@example.com")

    first = await _refresh(client, body["refresh_token"])
    assert first.status_code == 200

    replay = await _refresh(client, body["refresh_token"])
    assert replay.status_code == 401, replay.text
    assert "reuse" in replay.json()["detail"].lower()


async def test_reuse_of_rotated_token_revokes_whole_family(client, db_session):
    body = await _register(client, "reuse@example.com")
    first_jti = _jti(body["refresh_token"])

    second = (await _refresh(client, body["refresh_token"])).json()
    second_jti = _jti(second["refresh_token"])
    third = (await _refresh(client, second["refresh_token"])).json()
    third_jti = _jti(third["refresh_token"])

    replay = await _refresh(client, body["refresh_token"])
    assert replay.status_code == 401, replay.text
    assert "reuse" in replay.json()["detail"].lower()

    still_alive = await _refresh(client, third["refresh_token"])
    assert still_alive.status_code == 401, still_alive.text

    for jti in (first_jti, second_jti, third_jti):
        stored = await _stored(db_session, jti)
        assert stored.revoked_at is not None

    latest = await _stored(db_session, third_jti)
    assert latest.revoked_reason == REASON_REUSE


async def test_logout_revokes_refresh_token(client, db_session):
    body = await _register(client, "logout@example.com")
    jti = _jti(body["refresh_token"])

    logout = await client.post("/api/auth/logout", headers=_auth(body["access_token"]))
    assert logout.status_code == 204, logout.text

    stored = await _stored(db_session, jti)
    assert stored.revoked_at is not None
    assert stored.revoked_reason == REASON_LOGOUT

    resp = await _refresh(client, body["refresh_token"])
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Refresh token has been revoked"


async def test_logout_is_idempotent_and_kills_the_access_token(client, db_session):
    body = await _register(client, "logout-twice@example.com")

    first = await client.post("/api/auth/logout", headers=_auth(body["access_token"]))
    replayed = await client.post(
        "/api/auth/logout",
        headers=_auth(body["access_token"]),
        json={"refresh_token": body["refresh_token"]},
    )

    assert first.status_code == 204
    assert replayed.status_code == 401, (
        "после выхода access-токен обязан быть мёртв, иначе украденный токен живёт "
        f"ещё 15 минут: {replayed.status_code}"
    )

    login = await client.post(
        "/api/auth/login",
        json={"email": "logout-twice@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200, login.text
    fresh = login.json()
    again = await client.post(
        "/api/auth/logout",
        headers=_auth(fresh["access_token"]),
        json={"refresh_token": "garbage"},
    )
    assert again.status_code == 204, "повторный выход с мусорным refresh не должен падать"


async def test_logout_with_refresh_body_revokes_only_that_family(client, db_session):
    await _register(client, "two-sessions@example.com")
    login_a = (
        await client.post(
            "/api/auth/login",
            json={"email": "two-sessions@example.com", "password": PASSWORD},
        )
    ).json()
    login_b = (
        await client.post(
            "/api/auth/login",
            json={"email": "two-sessions@example.com", "password": PASSWORD},
        )
    ).json()

    logout = await client.post(
        "/api/auth/logout",
        headers=_auth(login_a["access_token"]),
        json={"refresh_token": login_a["refresh_token"]},
    )
    assert logout.status_code == 204, logout.text

    assert (await _refresh(client, login_a["refresh_token"])).status_code == 401
    assert (await _refresh(client, login_b["refresh_token"])).status_code == 200


async def test_logout_without_body_revokes_every_session(client):
    await _register(client, "all-sessions@example.com")
    login_a = (
        await client.post(
            "/api/auth/login",
            json={"email": "all-sessions@example.com", "password": PASSWORD},
        )
    ).json()
    login_b = (
        await client.post(
            "/api/auth/login",
            json={"email": "all-sessions@example.com", "password": PASSWORD},
        )
    ).json()

    logout = await client.post("/api/auth/logout", headers=_auth(login_a["access_token"]))
    assert logout.status_code == 204, logout.text

    assert (await _refresh(client, login_a["refresh_token"])).status_code == 401
    assert (await _refresh(client, login_b["refresh_token"])).status_code == 401


async def test_logout_cannot_revoke_another_users_session(client, db_session):
    victim = await _register(client, "victim@example.com")
    attacker = await _register(client, "attacker@example.com")

    logout = await client.post(
        "/api/auth/logout",
        headers=_auth(attacker["access_token"]),
        json={"refresh_token": victim["refresh_token"]},
    )
    assert logout.status_code == 204, logout.text

    assert (await _refresh(client, victim["refresh_token"])).status_code == 200
    assert (await _refresh(client, attacker["refresh_token"])).status_code == 401


async def test_logout_requires_authentication(client):
    resp = await client.post("/api/auth/logout")
    assert resp.status_code in (401, 403)


async def test_expired_refresh_token_returns_401(client, db_session):
    user = User(
        email="expired@example.com",
        password_hash=hash_password(PASSWORD),
        full_name="Expired",
    )
    db_session.add(user)
    await db_session.flush()

    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = create_refresh_token(
        user.id, jti="expired-jti", family_id="expired-fam", expires_at=past
    )
    db_session.add(
        RefreshToken(
            jti="expired-jti",
            family_id="expired-fam",
            user_id=user.id,
            expires_at=past,
        )
    )
    await db_session.flush()

    resp = await _refresh(client, token)
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Invalid or expired refresh token"


async def test_token_expired_in_db_but_not_in_jwt_returns_401(client, db_session):
    user = User(
        email="db-expired@example.com",
        password_hash=hash_password(PASSWORD),
        full_name="Db Expired",
    )
    db_session.add(user)
    await db_session.flush()

    future = datetime.now(timezone.utc) + timedelta(days=30)
    token = create_refresh_token(user.id, jti="stale-jti", family_id="stale-fam", expires_at=future)
    db_session.add(
        RefreshToken(
            jti="stale-jti",
            family_id="stale-fam",
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=5),
        )
    )
    await db_session.flush()

    resp = await _refresh(client, token)
    assert resp.status_code == 401, resp.text


@pytest.mark.parametrize(
    "token",
    ["", "not-a-jwt", "aaa.bbb.ccc"],
)
async def test_broken_refresh_token_returns_401(client, token):
    resp = await _refresh(client, token)
    assert resp.status_code == 401, resp.text


async def test_tampered_refresh_token_returns_401(client):
    body = await _register(client, "tampered@example.com")

    resp = await _refresh(client, body["refresh_token"] + "x")
    assert resp.status_code == 401, resp.text


async def test_access_token_is_not_accepted_as_refresh(client, db_session):
    body = await _register(client, "wrong-type@example.com")

    resp = await _refresh(client, body["access_token"])
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Invalid or expired refresh token"


async def test_signed_refresh_token_without_db_row_returns_401(client, db_session):
    user = User(
        email="phantom@example.com",
        password_hash=hash_password(PASSWORD),
        full_name="Phantom",
    )
    db_session.add(user)
    await db_session.flush()

    resp = await _refresh(client, create_refresh_token(user.id))
    assert resp.status_code == 401, resp.text


async def test_refresh_token_of_another_user_id_returns_401(client, db_session):
    body = await _register(client, "swapped@example.com")
    stored = await _stored(db_session, _jti(body["refresh_token"]))

    forged = create_refresh_token(stored.user_id + 1000, jti=stored.jti, family_id=stored.family_id)

    resp = await _refresh(client, forged)
    assert resp.status_code == 401, resp.text


async def test_deactivated_user_cannot_rotate(client, db_session):
    body = await _register(client, "deactivated-rotate@example.com")
    stored = await _stored(db_session, _jti(body["refresh_token"]))
    user = await db_session.get(User, stored.user_id)
    user.is_active = False
    await db_session.flush()

    resp = await _refresh(client, body["refresh_token"])
    assert resp.status_code == 401, resp.text


async def test_refresh_row_captures_user_agent_and_ip(client, db_session):
    resp = await client.post(
        "/api/auth/register",
        json={"email": "agent@example.com", "password": PASSWORD, "full_name": "Agent"},
        headers={"User-Agent": "BScoutTest/1.0"},
    )
    assert resp.status_code == 201, resp.text

    stored = await _stored(db_session, _jti(resp.json()["refresh_token"]))
    assert stored.user_agent == "BScoutTest/1.0"


async def test_register_does_not_confirm_existing_email(client):
    await _register(client, "enumerate@example.com")

    duplicate = await client.post(
        "/api/auth/register",
        json={"email": "enumerate@example.com", "password": PASSWORD, "full_name": "Other"},
    )

    assert duplicate.status_code == 409, duplicate.text
    detail = duplicate.json()["detail"].lower()
    assert "email" not in detail
    assert "registered" not in detail


async def test_login_detail_does_not_distinguish_missing_user_from_bad_password(client):
    await _register(client, "known-user@example.com")

    wrong_password = await client.post(
        "/api/auth/login",
        json={"email": "known-user@example.com", "password": "not-my-password"},
    )
    unknown_user = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": PASSWORD},
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json()["detail"] == unknown_user.json()["detail"]


async def test_password_longer_than_72_bytes_is_rejected(client):
    resp = await client.post(
        "/api/auth/register",
        json={"email": "long-pass@example.com", "password": "p" * 73, "full_name": "Long"},
    )

    assert resp.status_code == 422, resp.text
    assert "72 bytes" in resp.text


async def test_cyrillic_password_at_72_byte_boundary_is_accepted(client):
    password = "п" * 36
    assert len(password.encode("utf-8")) == 72

    resp = await client.post(
        "/api/auth/register",
        json={"email": "cyrillic-ok@example.com", "password": password, "full_name": "Кириллица"},
    )
    assert resp.status_code == 201, resp.text

    login = await client.post(
        "/api/auth/login",
        json={"email": "cyrillic-ok@example.com", "password": password},
    )
    assert login.status_code == 200, login.text


async def test_cyrillic_password_over_72_bytes_is_rejected(client):
    password = "п" * 37
    assert len(password) < 72
    assert len(password.encode("utf-8")) == 74

    resp = await client.post(
        "/api/auth/register",
        json={"email": "cyrillic-long@example.com", "password": password, "full_name": "Кир"},
    )

    assert resp.status_code == 422, resp.text


async def test_hash_password_refuses_silently_truncated_input():
    with pytest.raises(ValueError):
        hash_password("p" * 73)


async def test_revoked_family_token_reports_revoked_not_reuse(client, db_session):
    body = await _register(client, "revoked-detail@example.com")
    rotated = (await _refresh(client, body["refresh_token"])).json()

    await client.post("/api/auth/logout", headers=_auth(rotated["access_token"]))

    resp = await _refresh(client, rotated["refresh_token"])
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Refresh token has been revoked"


async def test_access_token_still_carries_sub_and_type(client, db_session):
    user = User(
        email="payload@example.com",
        password_hash=hash_password(PASSWORD),
        full_name="Payload",
    )
    db_session.add(user)
    await db_session.flush()

    payload = decode_token(create_access_token(user.id))
    assert payload["sub"] == str(user.id)
    assert payload["type"] == "access"
    assert "jti" not in payload


async def test_reuse_detection_survives_the_401_rollback(client, db_session):
    resp = await client.post(
        "/api/auth/register",
        json={"email": "reuse-durable@example.com", "password": PASSWORD, "full_name": "Reuse"},
    )
    stolen = resp.json()["refresh_token"]

    rotated = await client.post("/api/auth/refresh", json={"refresh_token": stolen})
    fresh = rotated.json()["refresh_token"]

    replayed = await client.post("/api/auth/refresh", json={"refresh_token": stolen})
    assert replayed.status_code == 401

    after = await client.post("/api/auth/refresh", json={"refresh_token": fresh})
    assert (
        after.status_code == 401
    ), "вся семья обязана быть отозвана, а не только предъявленный токен"

    rows = (
        (
            await db_session.execute(
                select(RefreshToken).where(RefreshToken.revoked_reason == "reuse_detected")
            )
        )
        .scalars()
        .all()
    )
    assert rows, "отзыв семьи должен пережить откат транзакции при 401"
