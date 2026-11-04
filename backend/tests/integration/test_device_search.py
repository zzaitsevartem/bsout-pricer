"""Device discovery and contextual categories use the same canonical catalog."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.catalog.model.catalog import Brand, Device, DeviceAlias, PartType, QualityTier
from src.modules.products.model.product import Cluster, Product, StoreOffer
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration


async def _catalog(db):
    user = User(
        email="device-search@example.com", password_hash=hash_password("test-device-pass"),
        full_name="Device search", is_active=True,
    )
    brand = Brand(name="Apple", slug="apple")
    tier = QualityTier(code="original", name_ru="Оригинал", rank=100)
    display = PartType(code="display", name_ru="Дисплей")
    battery = PartType(code="battery", name_ru="Аккумулятор")
    db.add_all([user, brand, tier, display, battery])
    await db.flush()
    now = datetime.now(timezone.utc)
    db.add(Subscription(
        user_id=user.id, plan=PlanEnum.advanced, start_date=now,
        end_date=now + timedelta(days=30), is_active=True,
    ))
    devices, products = {}, {}
    for variant in ("13", "13 Pro", "13 Pro Max", "13 mini", "113"):
        device = Device(
            brand_id=brand.id, name=f"iPhone {variant}",
            model_key="iphone-" + variant.lower().replace(" ", "-"),
        )
        db.add(device)
        await db.flush()
        devices[variant] = device
        db.add(DeviceAlias(device_id=device.id, alias=f"айфон {variant}", source="test"))
        for part in (display, battery) if variant == "13" else (display,):
            cluster = Cluster(device_id=device.id, part_type_id=part.id, offers_count=0)
            db.add(cluster)
            await db.flush()
            product = Product(
                cluster_id=cluster.id, quality_tier_id=tier.id, brand_id=brand.id,
                key_attrs={}, canonical_key=f"{device.model_key}|{part.code}",
                canonical_name=f"{part.name_ru} Apple iPhone {variant}",
            )
            db.add(product)
            await db.flush()
            products[variant, part.code] = product
    db.add(DeviceAlias(device_id=devices["13"].id, alias="ip13", source="test"))
    # Dictionary-only devices must not promise an empty catalog.
    db.add(Device(brand_id=brand.id, name="iPhone 13 empty", model_key="iphone-13-empty"))
    await db.commit()
    return {
        "headers": {"Authorization": f"Bearer {create_access_token(user.id)}"},
        "devices": devices, "display": display, "battery": battery, "products": products,
    }


@pytest.mark.parametrize("query", ["iphone 13", "айфон 13", "ip13", "iphone13"])
async def test_device_discovery_uses_aliases_and_ranks_exact_model(client, db_session, query):
    refs = await _catalog(db_session)
    response = await client.get(
        "/api/products/catalog/devices", params={"q": query}, headers=refs["headers"],
    )
    assert response.status_code == 200, response.text
    options = response.json()
    assert options[0] == {"id": refs["devices"]["13"].id, "label": "iPhone 13", "count": 2}
    assert all(option["label"] not in ("iPhone 113", "iPhone 13 empty") for option in options)


async def test_selected_device_spans_part_types_without_leaking_variants(client, db_session):
    refs = await _catalog(db_session)
    params = {"device_id": refs["devices"]["13"].id}
    response = await client.get("/api/products/catalog", params=params, headers=refs["headers"])
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 2
    facets = await client.get(
        "/api/products/catalog/facets", params=params, headers=refs["headers"],
    )
    assert facets.status_code == 200, facets.text
    assert {item["label"]: item["count"] for item in facets.json()["part_types"]} == {
        "Дисплей": 1, "Аккумулятор": 1,
    }
    params["part_type_id"] = refs["battery"].id
    narrowed = await client.get("/api/products/catalog", params=params, headers=refs["headers"])
    assert narrowed.status_code == 200, narrowed.text
    assert narrowed.json()["total"] == 1
    # Own-dimension exclusion leaves the other category available to switch to.
    categories = await client.get(
        "/api/products/catalog/facets", params=params, headers=refs["headers"],
    )
    assert len(categories.json()["part_types"]) == 2
    # Explicit Pro lock never resolves to Pro Max even though the text query is broad.
    pro = await client.get(
        "/api/products/catalog", params={"device_id": refs["devices"]["13 Pro"].id},
        headers=refs["headers"],
    )
    assert pro.status_code == 200, pro.text
    assert pro.json()["total"] == 1


async def test_device_query_validation_and_legacy_part_search(client, db_session):
    refs = await _catalog(db_session)
    for query in ("  ", "unknown-device-999"):
        response = await client.get(
            "/api/products/catalog/devices", params={"q": query}, headers=refs["headers"],
        )
        assert response.status_code == 200, response.text
        assert response.json() == []
    invalid = await client.get(
        "/api/products/catalog/devices", params={"q": "iphone", "limit": 9},
        headers=refs["headers"],
    )
    assert invalid.status_code == 422
    legacy = await client.get(
        "/api/products/catalog", params={"q": "iphone 13 аккумулятор"},
        headers=refs["headers"],
    )
    assert legacy.status_code == 200, legacy.text
    assert legacy.json()["total"] == 1
    invalid_range = await client.get(
        "/api/products/catalog/facets", params={"min_price": 100, "max_price": 1},
        headers=refs["headers"],
    )
    assert invalid_range.status_code == 422


async def test_categories_count_products_with_same_offer_filters_and_keep_selected_label(
    client, db_session,
):
    refs = await _catalog(db_session)
    stores = [
        Store(name=slug, slug=slug, website_url=f"https://{slug}.example.com", is_active=True)
        for slug in ("liberti", "profi")
    ]
    db_session.add_all(stores)
    await db_session.flush()
    display = refs["products"]["13", "display"]
    battery = refs["products"]["13", "battery"]
    # Two eligible offers for a single product must contribute just one category item.
    # Battery has cheap Profi + expensive Liberty: no single offer meets both constraints.
    for sku, product, store, price, stock in (
        ("display-a", display, stores[0], "100", "in_stock"),
        ("display-b", display, stores[0], "120", "low"),
        ("battery-cheap", battery, stores[1], "50", "in_stock"),
        ("battery-expensive", battery, stores[0], "900", "in_stock"),
        ("pro-display", refs["products"]["13 Pro", "display"], stores[0], "100", "in_stock"),
    ):
        db_session.add(StoreOffer(
            store_id=store.id, product_id=product.id, source_sku=sku, title=sku,
            normalized_title=sku, price_retail=Decimal(price), stock_status=stock,
            url=f"https://{store.slug}.example.com/{sku}", is_active=True, match_status="auto",
        ))
    await db_session.commit()
    params = {
        "device_id": refs["devices"]["13"].id, "store": "liberti",
        "max_price": 200, "in_stock": "true", "per_page": 1,
    }
    response = await client.get(
        "/api/products/catalog/facets", params=params, headers=refs["headers"],
    )
    assert response.status_code == 200, response.text
    assert response.json()["part_types"] == [
        {"id": refs["display"].id, "label": "Дисплей", "count": 1},
    ]
    offers = await client.get("/api/products", params=params, headers=refs["headers"])
    assert offers.status_code == 200, offers.text
    assert offers.json()["total"] == 2
    broad = await client.get(
        "/api/products", params={key: value for key, value in params.items() if key != "device_id"},
        headers=refs["headers"],
    )
    assert broad.status_code == 200, broad.text
    assert broad.json()["total"] == 3
    battery_offers = await client.get(
        "/api/products", params={**params, "part_type_id": refs["battery"].id},
        headers=refs["headers"],
    )
    assert battery_offers.status_code == 200, battery_offers.text
    assert battery_offers.json()["total"] == 0
    params["max_price"] = 1
    empty = await client.get(
        "/api/products/catalog/facets", params=params, headers=refs["headers"],
    )
    assert empty.status_code == 200, empty.text
    assert empty.json()["part_types"] == []
    assert empty.json()["devices"] == [
        {"id": refs["devices"]["13"].id, "label": "iPhone 13", "count": 0},
    ]


@pytest.mark.parametrize(
    "brand_name,model,alias",
    [("Samsung", "Galaxy S24", "самсунг с24"), ("Xiaomi", "Redmi Note 13", "редми ноут 13")],
)
async def test_device_search_and_catalog_are_brand_independent(
    client, db_session, brand_name, model, alias,
):
    refs = await _catalog(db_session)
    brand = Brand(name=brand_name, slug=brand_name.lower())
    db_session.add(brand)
    await db_session.flush()
    device = Device(brand_id=brand.id, name=model, model_key=model.lower().replace(" ", "-"))
    db_session.add(device)
    await db_session.flush()
    db_session.add(DeviceAlias(device_id=device.id, alias=alias, source="test"))
    cluster = Cluster(device_id=device.id, part_type_id=refs["display"].id, offers_count=0)
    db_session.add(cluster)
    await db_session.flush()
    db_session.add(Product(
        cluster_id=cluster.id, brand_id=brand.id, key_attrs={},
        canonical_key=f"{device.model_key}|display", canonical_name=f"Дисплей {model}",
    ))
    await db_session.commit()
    for query in (model, alias, f"{brand_name} {model}", f"{brand_name} {alias}"):
        suggestions = await client.get(
            "/api/products/catalog/devices", params={"q": query}, headers=refs["headers"],
        )
        assert suggestions.status_code == 200, suggestions.text
        assert suggestions.json() == [{"id": device.id, "label": model, "count": 1}]
    catalog = await client.get(
        "/api/products/catalog", params={"device_id": device.id}, headers=refs["headers"],
    )
    assert catalog.status_code == 200, catalog.text
    assert catalog.json()["total"] == 1
    facets = await client.get(
        "/api/products/catalog/facets", params={"device_id": device.id}, headers=refs["headers"],
    )
    assert facets.status_code == 200, facets.text
    assert facets.json()["part_types"] == [
        {"id": refs["display"].id, "label": "Дисплей", "count": 1},
    ]
