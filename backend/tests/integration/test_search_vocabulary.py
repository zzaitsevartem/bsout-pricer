from decimal import Decimal

import pytest
from sqlalchemy import literal, select

from src.modules.auth.model.user import PlanEnum, Subscription
from src.modules.categories.model.category import Category
from src.modules.products.service.search_predicate import search_predicate
from tests.integration.test_comparison_api import (
    _auth,
    _make_dictionaries,
    _make_offer,
    _make_product,
    _make_store,
    _make_user,
)

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("query", "positive", "negative"),
    [
        ("ddjlt yf lheujv zpsrt", "вводе на другом языке", "вводе на другом товаре"),
        ("съемный", "съёмный аккумулятор", "стационарный аккумулятор"),
        ("съёмный", "съемный аккумулятор", "стационарный аккумулятор"),
        ("емкость", "ёмкость батареи", "зарядная батарея"),
        ("ёмкость", "емкость батареи", "зарядка батареи"),
        ("plenka iPhone 15 Pro", "плёнка iphone 15 pro", "плёнка iphone 14 pro"),
        ("плёнка iphone 15", "plenka iphone 15 pro", "plenka ipad 15 pro"),
        ("shleyf", "шлейф iphone", "стекло iphone"),
        ("shleif", "шлейф iphone", "стекло iphone"),
        ("steklo", "стекло iphone", "шлейф iphone"),
        ("iphone SE", "iphone se", "iphone xr"),
        ("iphone XR", "iphone xr", "iphone se"),
        ("iphone 15 Pro", "iphone 15 pro", "iphone 15 processor"),
        ("samsung galaxy A52", "samsung galaxy a52", "samsung galaxy a53"),
        ("SM-A525", "SM-A525", "SM-A5250"),
        ("GT", "GT", "bright"),
        ("SKU-123", "SKU-123", "SKU-1234"),
        ("galaxy copy", "galaxy copy", "poco original"),
    ],
)
async def test_matching_and_competing_negatives(db_session, query, positive, negative):
    for fuzzy in (False, True):
        positive_match = await db_session.scalar(
            select(search_predicate(literal(positive), query, fuzzy))
        )
        negative_match = await db_session.scalar(
            select(search_predicate(literal(negative), query, fuzzy))
        )
        assert positive_match is True
        assert negative_match is False


async def test_basic_catalog_offers_facets_suggestions_filters_and_price_order(client, db_session):
    user, token = await _make_user(db_session)
    subscription = await db_session.scalar(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    subscription.plan = PlanEnum.basic
    refs = await _make_dictionaries(db_session)
    store = await _make_store(db_session, "vocab-a")
    other = await _make_store(db_session, "vocab-b")
    a = await _make_product(db_session, refs, refs["tier_copy"], "one", "Плёнка iPhone 15 Pro")
    b = await _make_product(db_session, refs, refs["tier_copy"], "two", "Пленка iPhone 15 Pro")
    c = await _make_product(db_session, refs, refs["tier_orig"], "three", "Пленка iPhone 14 Pro")
    category = Category(name="Parts", slug="vocab-parts")
    db_session.add(category)
    await db_session.flush()
    for product, owner, sku, price in (
        (a, store, "a", "200"),
        (b, store, "b", "100"),
        (c, other, "c", "150"),
    ):
        offer = await _make_offer(db_session, owner, product, sku, price)
        offer.category_id = category.id
        offer.title = product.canonical_name
        offer.normalized_title = product.canonical_name.lower()
    await db_session.flush()
    params = {
        "q": "plenka iphone 15 pro",
        "store": store.slug,
        "min_price": 90,
        "max_price": 210,
        "in_stock": "true",
        "device_id": refs["device"].id,
        "part_type_id": refs["part_type"].id,
        "quality_tier_id": refs["tier_copy"].id,
    }
    headers = _auth(token)
    response = await client.get("/api/products/catalog", params=params, headers=headers)
    assert response.status_code == 200, response.text
    assert [x["id"] for x in response.json()["results"]] == [b.id, a.id]
    response = await client.get(
        "/api/products/catalog",
        params={**params, "sort_by": "min_price_desc", "per_page": 1, "page": 2},
        headers=headers,
    )
    assert response.status_code == 200 and response.json()["results"][0]["id"] == b.id
    response = await client.get("/api/products", params=params, headers=headers)
    assert response.status_code == 200 and response.json()["total"] == 2
    facets = await client.get("/api/products/catalog/facets", params=params, headers=headers)
    assert facets.status_code == 200 and facets.json()["quality_tiers"]
    suggestions = await client.get(
        "/api/products/catalog/suggestions", params=params, headers=headers
    )
    assert suggestions.status_code == 200 and len(suggestions.json()) == 2
    for key, value in (
        ("store", "vocab-b"),
        ("device_id", 99999),
        ("part_type_id", 99999),
        ("quality_tier_id", refs["tier_orig"].id),
        ("min_price", 205),
        ("max_price", 95),
        ("in_stock", "false"),
    ):
        changed = {**params, key: value}
        if key == "min_price":
            changed["max_price"] = 210
        if key == "max_price":
            changed["min_price"] = 90
        for path in ("/api/products", "/api/products/catalog", "/api/products/catalog/suggestions"):
            result = await client.get(path, params=changed, headers=headers)
            assert result.status_code == 200, result.text
            body = result.json()
            rows = body["results"] if isinstance(body, dict) else body
            assert rows == [], (key, path, body)
    for category_name, expected in (("vocab-parts", 2), ("unknown-category", 0)):
        result = await client.get(
            "/api/products", params={**params, "category": category_name}, headers=headers
        )
        assert result.status_code == 200 and result.json()["total"] == expected
    result = await client.get(
        "/api/products/catalog/facets", params={**params, "store": "vocab-b"}, headers=headers
    )
    assert result.status_code == 200
    assert all(row["count"] == 0 for row in result.json()["quality_tiers"])
    empty = await client.get(
        "/api/products/catalog", params={**params, "min_price": Decimal("205")}, headers=headers
    )
    assert empty.status_code == 200 and empty.json()["total"] == 0


async def test_api_plan_policy_and_device_layout(client, db_session):
    user, token = await _make_user(db_session)
    subscription = await db_session.scalar(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    refs = await _make_dictionaries(db_session)
    store = await _make_store(db_session, "vocab-plan")
    product = await _make_product(db_session, refs, refs["tier_copy"], "plan", "Дисплей iPhone 13")
    offer = await _make_offer(db_session, store, product, "plan", "100")
    offer.title = product.canonical_name
    offer.normalized_title = product.canonical_name.lower()
    headers = _auth(token)
    for plan, expected in ((PlanEnum.basic, 0), (PlanEnum.advanced, 1)):
        subscription.plan = plan
        await db_session.flush()
        for path in ("/api/products", "/api/products/catalog", "/api/products/catalog/suggestions"):
            response = await client.get(path, params={"q": "dsplay iphone 13"}, headers=headers)
            assert response.status_code == 200, response.text
            body = response.json()
            rows = body["results"] if isinstance(body, dict) else body
            assert len(rows) == expected, (plan, path, body)
        for path in ("/api/products", "/api/products/catalog", "/api/products/catalog/suggestions"):
            response = await client.get(path, params={"q": "шзрщту 13"}, headers=headers)
            assert response.status_code == 200, response.text
            body = response.json()
            rows = body["results"] if isinstance(body, dict) else body
            assert len(rows) == 1, (plan, path, body)
    response = await client.get(
        "/api/products/catalog/devices", params={"q": "шзрщту 13"}, headers=headers
    )
    assert response.status_code == 200 and [row["id"] for row in response.json()] == [
        refs["device"].id
    ]
    response = await client.get(
        "/api/products/catalog/devices", params={"q": "шзрщту 14"}, headers=headers
    )
    assert response.status_code == 200 and response.json() == []
