import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def _register_and_login(client: AsyncClient) -> tuple[str, dict]:
    resp = await client.post("/api/auth/register", json={
        "email": "users@example.com",
        "password": "Secret123!",
        "full_name": "Users Test",
    })
    tokens = resp.json()
    return tokens["access_token"], tokens


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    access_token, _ = await _register_and_login(client)
    resp = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "users@example.com"
    assert data["full_name"] == "Users Test"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient):
    access_token, _ = await _register_and_login(client)
    resp = await client.patch(
        "/api/users/me",
        json={"full_name": "Updated Name", "phone": "+79991234567"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Updated Name"
    assert data["phone"] == "+79991234567"


@pytest.mark.asyncio
async def test_subscription_not_found(client: AsyncClient):
    access_token, _ = await _register_and_login(client)
    resp = await client.get(
        "/api/users/me/subscription",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_subscription(client: AsyncClient):
    access_token, _ = await _register_and_login(client)
    resp = await client.post(
        "/api/users/me/subscription",
        json={"plan": "trial"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["plan"] == "trial"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_subscription_twice_conflict(client: AsyncClient):
    access_token, _ = await _register_and_login(client)
    await client.post(
        "/api/users/me/subscription",
        json={"plan": "trial"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp = await client.post(
        "/api/users/me/subscription",
        json={"plan": "basic"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_subscription_after_creation(client: AsyncClient):
    access_token, _ = await _register_and_login(client)
    await client.post(
        "/api/users/me/subscription",
        json={"plan": "basic"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp = await client.get(
        "/api/users/me/subscription",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"] == "basic"
    assert data["is_active"] is True
