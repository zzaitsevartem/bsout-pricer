import pytest
import sqlalchemy as sa

from src.modules.auth.model.user import User
from src.modules.auth.service.auth import create_access_token, hash_password

pytestmark = pytest.mark.integration

VALID_PASSWORD = "s3cret-pass"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _register(
    client,
    email: str = "contract@example.com",
    password: str = VALID_PASSWORD,
    full_name: str = "Contract User",
    **extra,
) -> dict:
    payload = {"email": email, "password": password, "full_name": full_name, **extra}
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _register_and_token(client, email: str = "contract@example.com") -> str:
    body = await _register(client, email=email)
    return body["access_token"]


async def _make_admin(db_session, email: str = "admin@example.com") -> User:
    admin = User(
        email=email,
        password_hash=hash_password(VALID_PASSWORD),
        full_name="Admin User",
        is_active=True,
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.flush()
    return admin


async def test_health_returns_ok(client):
    resp = await client.get("/api/health")

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"status": "ok"}


async def test_register_returns_201_with_snake_case_tokens(client):
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "newbie@example.com",
            "password": VALID_PASSWORD,
            "full_name": "New Bie",
            "phone": "+79991234567",
            "company": "BScout",
        },
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert set(body) == {"access_token", "refresh_token", "token_type"}
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]


async def test_register_then_login_then_me_roundtrip(client):
    await _register(client, email="round@example.com", full_name="Round Trip")

    login = await client.post(
        "/api/auth/login",
        json={"identifier": "round@example.com", "password": VALID_PASSWORD},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    me = await client.get("/api/users/me", headers=_auth(token))
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["email"] == "round@example.com"
    assert body["full_name"] == "Round Trip"
    assert body["is_active"] is True
    assert body["is_admin"] is False
    assert isinstance(body["id"], int)
    assert "password_hash" not in body
    assert "password" not in body


async def test_register_same_email_twice_returns_409(client):
    await _register(client, email="dup@example.com")

    second = await client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": VALID_PASSWORD, "full_name": "Other"},
    )

    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "Registration could not be completed"


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": VALID_PASSWORD, "full_name": "Bad Email"},
        {"email": "short@example.com", "password": "12345", "full_name": "Short Pass"},
        {"email": "nofullname@example.com", "password": VALID_PASSWORD},
        {"password": VALID_PASSWORD, "full_name": "No Email"},
        {"email": "empty@example.com", "password": VALID_PASSWORD, "full_name": ""},
    ],
)
async def test_register_invalid_body_returns_422(client, payload):
    resp = await client.post("/api/auth/register", json=payload)

    assert resp.status_code == 422, resp.text
    assert isinstance(resp.json()["detail"], list)


async def test_login_with_wrong_password_returns_401(client):
    await _register(client, email="wrongpass@example.com")

    resp = await client.post(
        "/api/auth/login",
        json={"identifier": "wrongpass@example.com", "password": "totally-wrong"},
    )

    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Invalid login or password"


async def test_login_with_unknown_email_returns_401(client):
    resp = await client.post(
        "/api/auth/login",
        json={"identifier": "ghost@example.com", "password": VALID_PASSWORD},
    )

    assert resp.status_code == 401, resp.text


async def test_register_with_username_then_login_by_username(client):
    await _register(
        client,
        email="user@example.com",
        full_name="Login Owner",
        username="ivan.petrov",
    )

    by_username = await client.post(
        "/api/auth/login",
        json={"identifier": "Ivan.Petrov", "password": VALID_PASSWORD},
    )
    assert by_username.status_code == 200, by_username.text
    token = by_username.json()["access_token"]

    me = await client.get("/api/users/me", headers=_auth(token))
    assert me.status_code == 200, me.text
    assert me.json()["email"] == "user@example.com"

    by_email = await client.post(
        "/api/auth/login",
        json={"identifier": "user@example.com", "password": VALID_PASSWORD},
    )
    assert by_email.status_code == 200, by_email.text


async def test_register_same_username_twice_returns_409(client):
    await _register(client, email="fst@example.com", username="dup-login")

    second = await client.post(
        "/api/auth/register",
        json={
            "email": "snd@example.com",
            "password": VALID_PASSWORD,
            "full_name": "Other",
            "username": "DUP-LOGIN",
        },
    )

    assert second.status_code == 409, second.text


@pytest.mark.parametrize(
    "username",
    ["ab", "login with space", "log@in", "кириллица", "a" * 33],
)
async def test_register_invalid_username_returns_422(client, username):
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "baduser@example.com",
            "password": VALID_PASSWORD,
            "full_name": "Bad Login",
            "username": username,
        },
    )

    assert resp.status_code == 422, resp.text


async def test_username_available_endpoint(client):
    await _register(client, email="avail@example.com", username="taken.login")

    free = await client.get("/api/auth/username-available", params={"username": "free.login"})
    assert free.status_code == 200, free.text
    assert free.json() == {"available": True}

    taken = await client.get("/api/auth/username-available", params={"username": "TAKEN.LOGIN"})
    assert taken.status_code == 200, taken.text
    assert taken.json() == {"available": False}


async def test_cannot_change_username_within_cooldown(client, db_session):
    await _register(client, email="cooldown@example.com", username="first.login")
    login = await client.post(
        "/api/auth/login",
        json={"identifier": "cooldown@example.com", "password": VALID_PASSWORD},
    )
    token = login.json()["access_token"]
    headers = _auth(token)

    resp = await client.patch("/api/users/me", json={"username": "second.login"}, headers=headers)

    assert resp.status_code == 429, resp.text
    assert "5 минут" in resp.json()["detail"]


async def test_patch_me_duplicate_username_returns_409(client, db_session):
    await _register(client, email="first@example.com", username="shared.login")
    other = await client.post(
        "/api/auth/register",
        json={
            "email": "second@example.com",
            "password": VALID_PASSWORD,
            "full_name": "Other",
            "username": "other.login",
        },
    )
    token = other.json()["access_token"]

    from datetime import datetime, timedelta, timezone

    from src.modules.auth.model.user import User

    user = await db_session.execute(sa.select(User).where(User.email == "second@example.com"))
    user.scalar_one().username_changed_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    await db_session.flush()

    resp = await client.patch(
        "/api/users/me", json={"username": "SHARED.LOGIN"}, headers=_auth(token)
    )

    assert resp.status_code == 409, resp.text


async def test_products_on_empty_catalog_returns_empty_page(client):
    token = await _register_and_token(client, email="empty@example.com")

    resp = await client.get("/api/products", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["results"] == []
    assert body["total"] == 0
    assert body["page"] == 1
    assert body["per_page"] == 20


async def test_products_missing_offer_returns_404(client):
    token = await _register_and_token(client, email="missing@example.com")

    resp = await client.get("/api/products/999999", headers=_auth(token))

    assert resp.status_code == 404, resp.text
    assert resp.json()["detail"] == "Product not found"


async def test_products_price_history_of_missing_offer_returns_404(client):
    token = await _register_and_token(client, email="history404@example.com")

    resp = await client.get("/api/products/999999/price-history", headers=_auth(token))

    assert resp.status_code == 404, resp.text


async def test_products_reject_out_of_range_pagination(client):
    token = await _register_and_token(client, email="paging@example.com")

    assert (await client.get("/api/products?page=0", headers=_auth(token))).status_code == 422
    assert (await client.get("/api/products?per_page=101", headers=_auth(token))).status_code == 422


async def test_search_history_is_empty_list_for_new_user(client):
    token = await _register_and_token(client, email="history@example.com")

    resp = await client.get("/api/search/history", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json() == []


async def test_admin_stats_forbidden_for_regular_user(client):
    token = await _register_and_token(client, email="plain@example.com")

    resp = await client.get("/api/admin/stats", headers=_auth(token))

    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "Admin access required"


async def test_admin_stats_allowed_for_admin(client, db_session):
    admin = await _make_admin(db_session)
    token = create_access_token(admin.id)

    resp = await client.get("/api/admin/stats", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body == {
        "total_users": 1,
        "active_subscriptions": 0,
        "total_products": 0,
        "total_stores": 0,
    }


async def test_admin_parsers_forbidden_for_regular_user(client):
    token = await _register_and_token(client, email="notparser@example.com")

    resp = await client.get("/api/admin/parsers", headers=_auth(token))

    assert resp.status_code == 403, resp.text


async def test_public_stores_and_categories_are_readable_without_token(client):
    stores = await client.get("/api/stores")
    categories = await client.get("/api/categories")

    assert stores.status_code == 200, stores.text
    assert categories.status_code == 200, categories.text
    assert stores.json() == []
    assert categories.json() == []


async def test_public_detail_endpoints_return_404_for_missing_rows(client):
    store = await client.get("/api/stores/999999")
    category = await client.get("/api/categories/999999")

    assert store.status_code == 404, store.text
    assert store.json()["detail"] == "Store not found"
    assert category.status_code == 404, category.text
    assert category.json()["detail"] == "Category not found"


async def test_store_and_category_writes_require_admin(client):
    token = await _register_and_token(client, email="writer@example.com")

    store = await client.post(
        "/api/stores",
        headers=_auth(token),
        json={"name": "Shop", "slug": "shop", "website_url": "https://shop.example"},
    )
    category = await client.post(
        "/api/categories",
        headers=_auth(token),
        json={"name": "Displays", "slug": "displays"},
    )

    assert store.status_code == 403, store.text
    assert category.status_code == 403, category.text


async def test_admin_can_create_store_and_it_appears_in_public_list(client, db_session):
    admin = await _make_admin(db_session, email="storeadmin@example.com")
    token = create_access_token(admin.id)

    created = await client.post(
        "/api/stores",
        headers=_auth(token),
        json={"name": "Shop", "slug": "shop", "website_url": "https://shop.example"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["slug"] == "shop"

    duplicate = await client.post(
        "/api/stores",
        headers=_auth(token),
        json={"name": "Shop 2", "slug": "shop", "website_url": "https://shop2.example"},
    )
    assert duplicate.status_code == 409, duplicate.text

    listed = await client.get("/api/stores")
    assert [s["slug"] for s in listed.json()] == ["shop"]


async def test_protected_endpoints_without_authorization_header(client):
    for path in ("/api/users/me", "/api/products", "/api/search/history", "/api/admin/stats"):
        resp = await client.get(path)
        assert resp.status_code == 403, f"{path} -> {resp.status_code} {resp.text}"
        assert resp.json()["detail"] == "Not authenticated"


async def test_protected_endpoint_with_garbage_token_returns_401(client):
    resp = await client.get("/api/users/me", headers=_auth("not.a.jwt"))

    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Invalid or expired access token"


async def test_refresh_token_is_not_accepted_as_access_token(client):
    body = await _register(client, email="refresh@example.com")

    resp = await client.get("/api/users/me", headers=_auth(body["refresh_token"]))

    assert resp.status_code == 401, resp.text


async def test_inactive_user_is_rejected(client, db_session):
    body = await _register(client, email="inactive@example.com")
    user = (await client.get("/api/users/me", headers=_auth(body["access_token"]))).json()

    db_user = await db_session.get(User, user["id"])
    db_user.is_active = False
    await db_session.flush()

    resp = await client.get("/api/users/me", headers=_auth(body["access_token"]))

    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "User not found or inactive"


async def test_unknown_route_returns_404(client):
    resp = await client.get("/api/does-not-exist")

    assert resp.status_code == 404


async def test_admin_parser_run_returns_202_without_waiting_for_the_crawl(
    client, db_session, monkeypatch
):
    from importlib import import_module

    from src.modules.cache import RedisCache
    from src.modules.parser.service.parsers import register_default_parsers

    parser_service_module = import_module("src.modules.parser.service.parser_service")
    register_default_parsers()

    sent: list[tuple] = []

    async def fake_enqueue(slug, full_sync, limit, section=None):
        sent.append((slug, full_sync, limit, section))
        return "job-42"

    monkeypatch.setattr(parser_service_module, "enqueue_parser_run", fake_enqueue)
    await RedisCache.delete("parser:lock:tgsm")
    await RedisCache.delete("parser:status:tgsm")

    admin = await _make_admin(db_session, email="parserrun@example.com")
    token = create_access_token(admin.id)

    resp = await client.post(
        "/api/admin/parsers/run",
        json={"store_slug": "tgsm", "full_sync": True},
        headers=_auth(token),
    )

    assert resp.status_code == 202, resp.text
    assert resp.json() == {
        "store_slug": "tgsm",
        "status": "queued",
        "job_id": "job-42",
        "limit": None,
        "section": None,
    }
    assert sent == [("tgsm", True, None, None)]


async def test_admin_parser_run_rejects_unknown_store(client, db_session):
    admin = await _make_admin(db_session, email="parser404@example.com")
    token = create_access_token(admin.id)

    resp = await client.post(
        "/api/admin/parsers/run",
        json={"store_slug": "no-such-store"},
        headers=_auth(token),
    )

    assert resp.status_code == 404, resp.text
