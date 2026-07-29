import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "Secret123!",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "password": "Secret123!",
        "full_name": "User One",
    })
    resp = await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "password": "Secret456!",
        "full_name": "User Two",
    })
    assert resp.status_code == 409
    assert "already" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "login@example.com",
        "password": "Secret123!",
        "full_name": "Login User",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "Secret123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "wrong@example.com",
        "password": "Secret123!",
        "full_name": "Wrong User",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "Secret123!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient):
    register_resp = await client.post("/api/auth/register", json={
        "email": "refresh@example.com",
        "password": "Secret123!",
        "full_name": "Refresh User",
    })
    refresh_token = register_resp.json()["refresh_token"]

    resp = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post("/api/auth/refresh", json={
        "refresh_token": "invalid.jwt.token",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    register_resp = await client.post("/api/auth/register", json={
        "email": "logout@example.com",
        "password": "Secret123!",
        "full_name": "Logout User",
    })
    data = register_resp.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    resp = await client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 204
