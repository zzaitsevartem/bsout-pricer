import pytest

pytestmark = pytest.mark.integration


async def test_register_then_login_returns_tokens(client):
    reg = await client.post(
        "/api/auth/register",
        json={
            "email": "flow@example.com",
            "password": "s3cret-pass",
            "full_name": "Flow User",
        },
    )
    assert reg.status_code in (200, 201), reg.text

    login = await client.post(
        "/api/auth/login",
        json={"email": "flow@example.com", "password": "s3cret-pass"},
    )
    assert login.status_code == 200, login.text
    body = login.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_me_requires_auth(client):
    resp = await client.get("/api/users/me")
    assert resp.status_code in (401, 403)
