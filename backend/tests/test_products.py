from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.model.user import PlanEnum, Subscription
from src.modules.products.model.product import PriceHistory, Product
from src.modules.stores.model.store import Store
from src.modules.categories.model.category import Category


async def _seed_store(db: AsyncSession, name: str, slug: str) -> Store:
    store = Store(name=name, slug=slug, website_url=f"https://{slug}.test", is_active=True)
    db.add(store)
    await db.flush()
    return store


async def _seed_category(db: AsyncSession, name: str, slug: str) -> Category:
    cat = Category(name=name, slug=slug)
    db.add(cat)
    await db.flush()
    return cat


async def _seed_product(
    db: AsyncSession,
    store_id: int,
    category_id: int | None,
    name: str,
    price: float,
    in_stock: bool = True,
) -> Product:
    prod = Product(
        store_id=store_id,
        category_id=category_id,
        external_id=f"ext-{name.lower().replace(' ', '-')}",
        name=name,
        normalized_name=name.lower(),
        description=f"Description for {name}",
        price=price,
        currency="RUB",
        in_stock=in_stock,
        product_url=f"https://test.test/product/{name.lower().replace(' ', '-')}",
    )
    db.add(prod)
    await db.flush()
    return prod


async def _seed_price_history(db: AsyncSession, product_id: int, prices: list[tuple[float, int]]) -> None:
    now = datetime.now(timezone.utc)
    for price, days_ago in prices:
        ph = PriceHistory(
            product_id=product_id,
            price=price,
            recorded_at=now - timedelta(days=days_ago),
        )
        db.add(ph)
    await db.flush()


async def _register_and_subscribe(client: AsyncClient, db: AsyncSession, email: str) -> str:
    """Register user + create subscription. Returns access_token."""
    resp = await client.post("/api/auth/register", json={
        "email": email,
        "password": "TestPass123!",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]

    user_resp = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    user_id = user_resp.json()["id"]

    sub = Subscription(
        user_id=user_id,
        plan=PlanEnum.advanced,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
        auto_renew=True,
    )
    db.add(sub)
    await db.flush()

    return token


# ─── Preview limit (no auth) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_no_auth_preview_limit(client: AsyncClient, db_session: AsyncSession):
    """Non-authenticated users see max 3 products."""
    store = await _seed_store(db_session, "Preview Store", "preview-store")
    cat = await _seed_category(db_session, "Preview Cat", "preview-cat")
    for i in range(10):
        await _seed_product(db_session, store.id, cat.id, f"Товар {i}", 1000 + i * 100)

    resp = await client.get("/api/products")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 3
    assert data["total"] == 10  # total reflects actual count, results limited
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_search_no_auth_cannot_paginate(client: AsyncClient, db_session: AsyncSession):
    """Non-authenticated users always get page=1 with max 3 results."""
    store = await _seed_store(db_session, "Pag Store", "pag-store")
    cat = await _seed_category(db_session, "Pag Cat", "pag-cat")
    for i in range(10):
        await _seed_product(db_session, store.id, cat.id, f"Товар {i}", 1000 + i * 100)

    resp = await client.get("/api/products?page=2&per_page=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 3
    assert data["page"] == 1
    assert data["per_page"] == 3


# ─── Search with active subscription ──────────────────────────────────


@pytest.mark.asyncio
async def test_search_with_subscription_full_access(client: AsyncClient, db_session: AsyncSession):
    """Subscribed users see all products and can paginate."""
    token = await _register_and_subscribe(client, db_session, "full@test.ru")

    store = await _seed_store(db_session, "Full Store", "full-store")
    cat = await _seed_category(db_session, "Full Cat", "full-cat")
    for i in range(10):
        await _seed_product(db_session, store.id, cat.id, f"Товар {i}", 1000 + i * 100)

    resp = await client.get("/api/products", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 10

    resp = await client.get("/api/products?page=2&per_page=5", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    assert len(data["results"]) == 5
    assert data["page"] == 2
    assert data["per_page"] == 5


@pytest.mark.asyncio
async def test_search_with_subscription_filters(client: AsyncClient, db_session: AsyncSession):
    """Subscribed users can use all filters."""
    token = await _register_and_subscribe(client, db_session, "filters@test.ru")

    store = await _seed_store(db_session, "Filter Store", "filter-store")
    cat = await _seed_category(db_session, "Filter Cat", "filter-cat")
    await _seed_product(db_session, store.id, cat.id, "Ноутбук ASUS", 50_000)
    await _seed_product(db_session, store.id, cat.id, "Ноутбук Lenovo", 45_000)
    await _seed_product(db_session, store.id, cat.id, "Мышь Logitech", 2_500)

    headers = {"Authorization": f"Bearer {token}"}

    # Query filter
    resp = await client.get("/api/products?q=ноутбук", headers=headers)
    assert resp.json()["total"] == 2

    # Store filter
    resp = await client.get("/api/products?store=filter-store", headers=headers)
    assert resp.json()["total"] == 3

    # Category filter
    resp = await client.get("/api/products?category=filter-cat", headers=headers)
    assert resp.json()["total"] == 3

    # No matches
    resp = await client.get("/api/products?q=nonexistent", headers=headers)
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_price_filter(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_subscribe(client, db_session, "pfilter@test.ru")
    h = {"Authorization": f"Bearer {token}"}

    store = await _seed_store(db_session, "P Store", "p-store")
    cat = await _seed_category(db_session, "P Cat", "p-cat")
    await _seed_product(db_session, store.id, cat.id, "Дешёвый", 1_000)
    await _seed_product(db_session, store.id, cat.id, "Средний", 5_000)
    await _seed_product(db_session, store.id, cat.id, "Дорогой", 10_000)

    assert (await client.get("/api/products?min_price=5000", headers=h)).json()["total"] == 2
    assert (await client.get("/api/products?max_price=5000", headers=h)).json()["total"] == 2
    assert (await client.get("/api/products?min_price=2000&max_price=8000", headers=h)).json()["total"] == 1


@pytest.mark.asyncio
async def test_search_in_stock_filter(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_subscribe(client, db_session, "stockf@test.ru")
    h = {"Authorization": f"Bearer {token}"}

    store = await _seed_store(db_session, "S Store", "s-store")
    cat = await _seed_category(db_session, "S Cat", "s-cat")
    await _seed_product(db_session, store.id, cat.id, "В наличии", 1_000, in_stock=True)
    await _seed_product(db_session, store.id, cat.id, "Нет в наличии", 500, in_stock=False)

    data = (await client.get("/api/products?store=s-store&in_stock=true", headers=h)).json()
    assert data["total"] == 1
    assert data["results"][0]["in_stock"] is True

    data = (await client.get("/api/products?store=s-store&in_stock=false", headers=h)).json()
    assert data["total"] == 1
    assert data["results"][0]["in_stock"] is False


@pytest.mark.asyncio
async def test_search_sort(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_subscribe(client, db_session, "sort@test.ru")
    h = {"Authorization": f"Bearer {token}"}

    store = await _seed_store(db_session, "S2 Store", "s2-store")
    cat = await _seed_category(db_session, "S2 Cat", "s2-cat")
    await _seed_product(db_session, store.id, cat.id, "A", 10_000)
    await _seed_product(db_session, store.id, cat.id, "B", 1_000)
    await _seed_product(db_session, store.id, cat.id, "C", 5_000)

    # Price asc
    prices = [float(r["price"]) for r in (await client.get("/api/products?sort_by=price_asc", headers=h)).json()["results"]]
    assert prices == sorted(prices)
    assert prices[0] == 1000.0

    # Price desc
    prices = [float(r["price"]) for r in (await client.get("/api/products?sort_by=price_desc", headers=h)).json()["results"]]
    assert prices == sorted(prices, reverse=True)
    assert prices[0] == 10000.0


@pytest.mark.asyncio
async def test_search_is_cheapest_flag(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_subscribe(client, db_session, "cheap@test.ru")
    h = {"Authorization": f"Bearer {token}"}

    store = await _seed_store(db_session, "C Store", "c-store")
    cat = await _seed_category(db_session, "C Cat", "c-cat")
    p2 = await _seed_product(db_session, store.id, cat.id, "Дешёвый", 1_000)
    await _seed_product(db_session, store.id, cat.id, "Дорогой", 10_000)

    results = (await client.get("/api/products", headers=h)).json()["results"]
    cheap = [r for r in results if r["is_cheapest"]]
    assert len(cheap) == 1
    assert float(cheap[0]["price"]) == 1000.0
    assert cheap[0]["id"] == p2.id


# ─── Product detail ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_product_detail_not_found(client: AsyncClient):
    resp = await client.get("/api/products/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_product_detail_without_auth(client: AsyncClient, db_session: AsyncSession):
    """Single product detail is public (no auth needed)."""
    store = await _seed_store(db_session, "D Store", "d-store")
    product = await _seed_product(db_session, store.id, None, "Тестовый товар", 7_500)

    resp = await client.get(f"/api/products/{product.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == product.id
    assert data["name"] == "Тестовый товар"
    assert data["store"] is not None
    assert data["store"]["name"] == "D Store"


@pytest.mark.asyncio
async def test_product_detail_with_auth(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_subscribe(client, db_session, "detail@test.ru")
    h = {"Authorization": f"Bearer {token}"}

    store = await _seed_store(db_session, "D2 Store", "d2-store")
    product = await _seed_product(db_session, store.id, None, "Товар авторизованный", 5_000)

    resp = await client.get(f"/api/products/{product.id}", headers=h)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Товар авторизованный"
    assert float(data["price"]) == 5000.0


# ─── Price history ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_price_history_requires_subscription(client: AsyncClient, db_session: AsyncSession):
    """Price history requires active subscription."""
    store = await _seed_store(db_session, "PH Store", "ph-store")
    product = await _seed_product(db_session, store.id, None, "PH Product", 1_000)

    resp = await client.get(f"/api/products/{product.id}/price-history")
    assert resp.status_code == 403
    assert "subscription" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_price_history_not_found(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_subscribe(client, db_session, "ph-nf@test.ru")
    resp = await client.get("/api/products/99999/price-history", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_price_history_empty(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_subscribe(client, db_session, "ph-empty@test.ru")
    h = {"Authorization": f"Bearer {token}"}

    store = await _seed_store(db_session, "PH2 Store", "ph2-store")
    product = await _seed_product(db_session, store.id, None, "Без истории", 1_000)

    resp = await client.get(f"/api/products/{product.id}/price-history", headers=h)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_price_history_with_data(client: AsyncClient, db_session: AsyncSession):
    token = await _register_and_subscribe(client, db_session, "ph-data@test.ru")
    h = {"Authorization": f"Bearer {token}"}

    store = await _seed_store(db_session, "PH3 Store", "ph3-store")
    product = await _seed_product(db_session, store.id, None, "С историей", 3_000)
    await _seed_price_history(db_session, product.id, [
        (2_500, 30), (2_800, 20), (3_000, 10), (2_700, 5),
    ])

    resp = await client.get(f"/api/products/{product.id}/price-history", headers=h)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    prices = [d["price"] for d in data]
    assert prices == ["2500.00", "2800.00", "3000.00", "2700.00"]
    for entry in data:
        assert "id" in entry and "price" in entry and "recorded_at" in entry
        assert entry["product_id"] == product.id
