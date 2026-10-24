from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.catalog.model.catalog import Brand, Device, PartType, QualityTier
from src.modules.products.model.product import (
    Cluster,
    OfferPriceHistory,
    Product,
    StoreOffer,
)
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(db, email: str = "cmp@example.com") -> tuple[User, str]:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Comparison User",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    now = datetime.now(timezone.utc)
    db.add(
        Subscription(
            user_id=user.id,
            plan=PlanEnum.advanced,
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True,
        )
    )
    await db.flush()

    return user, create_access_token(user.id)


async def _make_dictionaries(db) -> dict:
    brand = Brand(name="Apple", slug="apple")
    db.add(brand)
    await db.flush()

    device = Device(brand_id=brand.id, name="iPhone 13", model_key="apple-iphone-13")
    part_type = PartType(code="display", name_ru="Дисплей")
    db.add_all([device, part_type])
    await db.flush()

    tier_copy = QualityTier(code="copy", name_ru="Копия", rank=10)
    tier_orig = QualityTier(code="original", name_ru="Оригинал", rank=100)
    db.add_all([tier_copy, tier_orig])
    await db.flush()

    cluster = Cluster(device_id=device.id, part_type_id=part_type.id, offers_count=0)
    db.add(cluster)
    await db.flush()

    return {
        "brand": brand,
        "device": device,
        "part_type": part_type,
        "tier_copy": tier_copy,
        "tier_orig": tier_orig,
        "cluster": cluster,
    }


async def _make_product(db, refs: dict, tier, suffix: str, name: str) -> Product:
    product = Product(
        cluster_id=refs["cluster"].id,
        quality_tier_id=tier.id,
        brand_id=refs["brand"].id,
        key_attrs={"color": None},
        canonical_key=f"apple-iphone-13|display|{suffix}|-",
        canonical_name=name,
    )
    db.add(product)
    await db.flush()
    return product


async def _make_store(db, slug: str) -> Store:
    store = Store(
        name=slug.upper(), slug=slug, website_url=f"http://{slug}.example.com", is_active=True
    )
    db.add(store)
    await db.flush()
    return store


async def _make_offer(
    db,
    store: Store,
    product: Product | None,
    sku: str,
    price: str,
    price_opt: str | None = None,
    is_active: bool = True,
    stock_status: str = "in_stock",
) -> StoreOffer:
    offer = StoreOffer(
        store_id=store.id,
        product_id=product.id if product else None,
        source_sku=sku,
        title=f"Offer {sku}",
        normalized_title=f"offer {sku}".lower(),
        price_retail=Decimal(price),
        price_opt=Decimal(price_opt) if price_opt else None,
        price_old=Decimal("9999.00"),
        stock_status=stock_status,
        url=f"http://{store.slug}.example.com/{sku}",
        is_active=is_active,
        match_status="auto" if product else "unmatched",
    )
    db.add(offer)
    await db.flush()
    return offer


async def test_catalog_requires_auth(client):
    resp = await client.get("/api/products/catalog")

    assert resp.status_code == 403, resp.text


async def test_catalog_detail_and_history_require_auth(client):
    detail = await client.get("/api/products/catalog/1")
    history = await client.get("/api/products/catalog/1/price-history")

    assert detail.status_code == 403, detail.text
    assert history.status_code == 403, history.text


async def test_catalog_is_empty_when_no_canonical_products(client, db_session):
    _, token = await _make_user(db_session)

    resp = await client.get("/api/products/catalog", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body == {"results": [], "total": 0, "page": 1, "per_page": 20}


async def test_catalog_returns_product_without_offers_with_null_prices(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    await _make_product(db_session, refs, refs["tier_copy"], "copy", "Дисплей iPhone 13 копия")

    resp = await client.get("/api/products/catalog", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    item = body["results"][0]
    assert item["min_price_retail"] is None
    assert item["offers_count"] == 0
    assert item["stores_count"] == 0
    assert item["store_slugs"] == []


async def test_catalog_aggregates_offers_from_three_stores(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(
        db_session, refs, refs["tier_copy"], "copy", "Дисплей iPhone 13 копия"
    )

    store_a = await _make_store(db_session, "store-a")
    store_b = await _make_store(db_session, "store-b")
    store_c = await _make_store(db_session, "store-c")
    await _make_offer(db_session, store_a, product, "A1", "5000.00", "4500.00")
    await _make_offer(db_session, store_b, product, "B1", "4200.00", "3900.00")
    await _make_offer(db_session, store_c, product, "C1", "6100.00")

    resp = await client.get("/api/products/catalog", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    item = resp.json()["results"][0]
    assert item["id"] == product.id
    assert item["canonical_key"] == "apple-iphone-13|display|copy|-"
    assert item["min_price_retail"] == "4200.00"
    assert item["min_price_opt"] == "3900.00"
    assert item["offers_count"] == 3
    assert item["stores_count"] == 3
    assert item["store_slugs"] == ["store-a", "store-b", "store-c"]
    assert item["brand"]["slug"] == "apple"
    assert item["device"]["model_key"] == "apple-iphone-13"
    assert item["part_type"]["code"] == "display"
    assert item["quality_tier"]["code"] == "copy"


async def test_catalog_ignores_inactive_and_unlinked_offers(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(
        db_session, refs, refs["tier_copy"], "copy", "Дисплей iPhone 13 копия"
    )

    store_a = await _make_store(db_session, "store-a")
    store_b = await _make_store(db_session, "store-b")
    await _make_offer(db_session, store_a, product, "A1", "5000.00")
    await _make_offer(db_session, store_b, product, "B1", "1000.00", is_active=False)
    await _make_offer(db_session, store_b, None, "B2", "10.00")

    resp = await client.get("/api/products/catalog", headers=_auth(token))

    item = resp.json()["results"][0]
    assert item["min_price_retail"] == "5000.00"
    assert item["offers_count"] == 1
    assert item["stores_count"] == 1


async def test_catalog_filters_by_q_device_part_type_and_quality(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    copy_product = await _make_product(
        db_session, refs, refs["tier_copy"], "copy", "Дисплей iPhone 13 копия"
    )
    orig_product = await _make_product(
        db_session, refs, refs["tier_orig"], "original", "Дисплей iPhone 13 оригинал"
    )

    by_q = await client.get("/api/products/catalog?q=оригинал", headers=_auth(token))
    assert by_q.status_code == 200, by_q.text
    assert [r["id"] for r in by_q.json()["results"]] == [orig_product.id]
    assert by_q.json()["total"] == 1

    by_quality = await client.get(
        f"/api/products/catalog?quality_tier_id={refs['tier_copy'].id}", headers=_auth(token)
    )
    assert [r["id"] for r in by_quality.json()["results"]] == [copy_product.id]

    by_device = await client.get(
        f"/api/products/catalog?device_id={refs['device'].id}", headers=_auth(token)
    )
    assert by_device.json()["total"] == 2

    by_missing_device = await client.get(
        f"/api/products/catalog?device_id={refs['device'].id + 999}", headers=_auth(token)
    )
    assert by_missing_device.json()["total"] == 0

    by_part_type = await client.get(
        f"/api/products/catalog?part_type_id={refs['part_type'].id}", headers=_auth(token)
    )
    assert by_part_type.json()["total"] == 2


async def test_catalog_sorting_and_pagination(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    cheap = await _make_product(db_session, refs, refs["tier_copy"], "copy", "Дисплей копия")
    pricey = await _make_product(
        db_session, refs, refs["tier_orig"], "original", "Дисплей оригинал"
    )

    store = await _make_store(db_session, "store-a")
    await _make_offer(db_session, store, cheap, "A1", "1000.00")
    await _make_offer(db_session, store, pricey, "A2", "9000.00")

    asc = await client.get("/api/products/catalog?sort_by=min_price_asc", headers=_auth(token))
    desc = await client.get("/api/products/catalog?sort_by=min_price_desc", headers=_auth(token))

    assert [r["id"] for r in asc.json()["results"]] == [cheap.id, pricey.id]
    assert [r["id"] for r in desc.json()["results"]] == [pricey.id, cheap.id]

    page_one = await client.get("/api/products/catalog?per_page=1&page=1", headers=_auth(token))
    page_two = await client.get("/api/products/catalog?per_page=1&page=2", headers=_auth(token))

    assert page_one.json()["total"] == 2
    assert [r["id"] for r in page_one.json()["results"]] == [cheap.id]
    assert [r["id"] for r in page_two.json()["results"]] == [pricey.id]


async def test_comparison_detail_returns_offers_sorted_with_stats(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(
        db_session, refs, refs["tier_copy"], "copy", "Дисплей iPhone 13 копия"
    )

    store_a = await _make_store(db_session, "store-a")
    store_b = await _make_store(db_session, "store-b")
    store_c = await _make_store(db_session, "store-c")
    await _make_offer(db_session, store_a, product, "A1", "5000.00", "4500.00")
    await _make_offer(db_session, store_b, product, "B1", "4000.00", "3600.00")
    await _make_offer(db_session, store_c, product, "C1", "6000.00")

    resp = await client.get(f"/api/products/catalog/{product.id}", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["product"]["id"] == product.id
    assert body["cluster"]["id"] == refs["cluster"].id
    assert body["cluster"]["device_id"] == refs["device"].id

    prices = [o["price_retail"] for o in body["offers"]]
    assert prices == ["4000.00", "5000.00", "6000.00"]
    assert [o["store"]["slug"] for o in body["offers"]] == ["store-b", "store-a", "store-c"]
    assert [o["is_cheapest"] for o in body["offers"]] == [True, False, False]
    assert body["offers"][0]["price_old"] == "9999.00"
    assert body["offers"][0]["stock_status"] == "in_stock"
    assert body["offers"][0]["url"].endswith("/B1")
    assert body["offers"][0]["last_seen_at"] is not None

    stats = body["stats"]
    assert stats["offers_count"] == 3
    assert stats["stores_count"] == 3
    assert stats["min_price_retail"] == "4000.00"
    assert stats["max_price_retail"] == "6000.00"
    assert stats["avg_price_retail"] == "5000.00"
    assert stats["min_price_opt"] == "3600.00"
    assert stats["spread_abs"] == "2000.00"
    assert stats["spread_pct"] == 50.0


async def test_comparison_detail_without_offers_has_empty_stats(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, refs["tier_copy"], "copy", "Дисплей копия")

    resp = await client.get(f"/api/products/catalog/{product.id}", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["offers"] == []
    assert body["alternatives"] == []
    assert body["stats"]["offers_count"] == 0
    assert body["stats"]["stores_count"] == 0
    assert body["stats"]["min_price_retail"] is None
    assert body["stats"]["spread_pct"] is None


async def test_comparison_detail_lists_alternative_quality_tiers_in_cluster(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    copy_product = await _make_product(
        db_session, refs, refs["tier_copy"], "copy", "Дисплей iPhone 13 копия"
    )
    orig_product = await _make_product(
        db_session, refs, refs["tier_orig"], "original", "Дисплей iPhone 13 оригинал"
    )

    store_a = await _make_store(db_session, "store-a")
    store_b = await _make_store(db_session, "store-b")
    await _make_offer(db_session, store_a, copy_product, "A1", "4000.00")
    await _make_offer(db_session, store_a, orig_product, "A2", "12000.00", "11000.00")
    await _make_offer(db_session, store_b, orig_product, "B2", "11500.00")

    resp = await client.get(f"/api/products/catalog/{copy_product.id}", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    alternatives = resp.json()["alternatives"]
    assert len(alternatives) == 1
    alt = alternatives[0]
    assert alt["product_id"] == orig_product.id
    assert alt["quality_tier"]["code"] == "original"
    assert alt["min_price_retail"] == "11500.00"
    assert alt["min_price_opt"] == "11000.00"
    assert alt["offers_count"] == 2
    assert alt["stores_count"] == 2


async def test_comparison_alternatives_exclude_other_clusters(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, refs["tier_copy"], "copy", "Дисплей копия")

    other_part = PartType(code="battery", name_ru="Аккумулятор")
    db_session.add(other_part)
    await db_session.flush()
    other_cluster = Cluster(device_id=refs["device"].id, part_type_id=other_part.id)
    db_session.add(other_cluster)
    await db_session.flush()
    db_session.add(
        Product(
            cluster_id=other_cluster.id,
            quality_tier_id=refs["tier_copy"].id,
            brand_id=refs["brand"].id,
            canonical_key="apple-iphone-13|battery|copy|-",
            canonical_name="Аккумулятор iPhone 13 копия",
        )
    )
    await db_session.flush()

    resp = await client.get(f"/api/products/catalog/{product.id}", headers=_auth(token))

    assert resp.json()["alternatives"] == []


async def test_comparison_detail_404_for_unknown_product(client, db_session):
    _, token = await _make_user(db_session)

    resp = await client.get("/api/products/catalog/424242", headers=_auth(token))

    assert resp.status_code == 404, resp.text
    assert resp.json()["detail"] == "Canonical product not found"


async def test_price_history_aggregates_daily_minimum_across_stores(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, refs["tier_copy"], "copy", "Дисплей копия")

    store_a = await _make_store(db_session, "store-a")
    store_b = await _make_store(db_session, "store-b")
    offer_a = await _make_offer(db_session, store_a, product, "A1", "5000.00")
    offer_b = await _make_offer(db_session, store_b, product, "B1", "4800.00")

    now = datetime.now(timezone.utc)
    day_one = (now - timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
    day_two = (now - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)

    db_session.add_all(
        [
            OfferPriceHistory(
                offer_id=offer_a.id,
                price_retail=Decimal("5200.00"),
                stock_status="in_stock",
                recorded_at=day_one,
            ),
            OfferPriceHistory(
                offer_id=offer_b.id,
                price_retail=Decimal("5100.00"),
                stock_status="in_stock",
                recorded_at=day_one,
            ),
            OfferPriceHistory(
                offer_id=offer_a.id,
                price_retail=Decimal("5000.00"),
                stock_status="in_stock",
                recorded_at=day_two,
            ),
            OfferPriceHistory(
                offer_id=offer_b.id,
                price_retail=Decimal("4800.00"),
                stock_status="in_stock",
                recorded_at=day_two,
            ),
        ]
    )
    await db_session.flush()

    resp = await client.get(
        f"/api/products/catalog/{product.id}/price-history", headers=_auth(token)
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["product_id"] == product.id
    assert body["days"] == 90

    points = body["points"]
    assert len(points) == 2
    assert points[0]["day"] == day_one.date().isoformat()
    assert points[0]["min_price_retail"] == "5100.00"
    assert points[0]["max_price_retail"] == "5200.00"
    assert points[0]["avg_price_retail"] == "5150.00"
    assert points[0]["stores_count"] == 2
    assert points[1]["day"] == day_two.date().isoformat()
    assert points[1]["min_price_retail"] == "4800.00"
    assert points[0]["day"] < points[1]["day"]


async def test_price_history_respects_days_window(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, refs["tier_copy"], "copy", "Дисплей копия")

    store = await _make_store(db_session, "store-a")
    offer = await _make_offer(db_session, store, product, "A1", "5000.00")

    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            OfferPriceHistory(
                offer_id=offer.id,
                price_retail=Decimal("100.00"),
                stock_status="in_stock",
                recorded_at=now - timedelta(days=200),
            ),
            OfferPriceHistory(
                offer_id=offer.id,
                price_retail=Decimal("500.00"),
                stock_status="in_stock",
                recorded_at=now - timedelta(days=2),
            ),
        ]
    )
    await db_session.flush()

    default_window = await client.get(
        f"/api/products/catalog/{product.id}/price-history", headers=_auth(token)
    )
    wide_window = await client.get(
        f"/api/products/catalog/{product.id}/price-history?days=365", headers=_auth(token)
    )

    assert len(default_window.json()["points"]) == 1
    assert default_window.json()["points"][0]["min_price_retail"] == "500.00"
    assert wide_window.json()["days"] == 365
    assert len(wide_window.json()["points"]) == 2


async def test_price_history_empty_for_product_without_history(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, refs["tier_copy"], "copy", "Дисплей копия")

    resp = await client.get(
        f"/api/products/catalog/{product.id}/price-history", headers=_auth(token)
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["points"] == []


async def test_price_history_404_for_unknown_product(client, db_session):
    _, token = await _make_user(db_session)

    resp = await client.get("/api/products/catalog/424242/price-history", headers=_auth(token))

    assert resp.status_code == 404, resp.text


async def test_catalog_routes_declared_before_offer_id_route(client, db_session):
    _, token = await _make_user(db_session)

    catalog = await client.get("/api/products/catalog", headers=_auth(token))

    assert catalog.status_code == 200, catalog.text
    assert catalog.status_code != 422
    assert "results" in catalog.json()

    from src.modules.products.controller.products import router

    paths = [route.path for route in router.routes]
    offer_index = paths.index("/api/products/{offer_id}")
    assert paths.index("/api/products/catalog") < offer_index
    assert paths.index("/api/products/catalog/{product_id}") < offer_index
    assert paths.index("/api/products/catalog/{product_id}/price-history") < offer_index


async def test_offer_endpoint_still_works_after_catalog_routes(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, refs["tier_copy"], "copy", "Дисплей копия")
    store = await _make_store(db_session, "store-a")
    offer = await _make_offer(db_session, store, product, "A1", "5000.00")

    resp = await client.get(f"/api/products/{offer.id}", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == offer.id
    assert resp.json()["product_id"] == product.id


async def test_catalog_offer_filters_share_offer_and_filter_aggregates(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    store_a = await _make_store(db_session, "store-a")
    store_b = await _make_store(db_session, "store-b")
    products = [
        await _make_product(db_session, refs, refs["tier_copy"], str(i), f"Display {i}")
        for i in range(5)
    ]
    await _make_offer(db_session, store_a, products[0], "A0", "100", "90")
    await _make_offer(db_session, store_a, products[0], "A1", "200", "180", stock_status="low")
    await _make_offer(db_session, store_b, products[0], "B0", "50", "40")
    await _make_offer(db_session, store_a, products[0], "A2", "150", stock_status="out")
    await _make_offer(db_session, store_a, products[1], "A3", "500")
    await _make_offer(db_session, store_b, products[1], "B1", "100")
    await _make_offer(db_session, store_a, products[2], "A4", "100", stock_status="out")
    await _make_offer(db_session, store_a, products[2], "A5", "500")
    await _make_offer(db_session, store_a, products[3], "A6", "200", stock_status="low")
    params = {"store": "store-a", "min_price": "100", "max_price": "200", "in_stock": "true"}
    response = await client.get("/api/products/catalog", params=params, headers=_auth(token))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 2
    assert [item["id"] for item in body["results"]] == [products[0].id, products[3].id]
    item = body["results"][0]
    assert item["min_price_retail"] == "100.00"
    assert item["min_price_opt"] == "90.00"
    assert item["offers_count"] == 2
    assert item["stores_count"] == 1
    assert item["store_slugs"] == ["store-a"]
    for page, expected in [(1, products[0].id), (2, products[3].id), (3, None)]:
        response = await client.get(
            "/api/products/catalog",
            params={**params, "page": page, "per_page": 1},
            headers=_auth(token),
        )
        assert response.json()["total"] == 2
        assert [row["id"] for row in response.json()["results"]] == ([expected] if expected else [])
    detail = await client.get(f"/api/products/catalog/{products[0].id}", headers=_auth(token))
    assert detail.json()["stats"]["offers_count"] == 4
    assert detail.json()["stats"]["min_price_retail"] == "50.00"
    missing = await client.get(
        "/api/products/catalog", params={"store": "missing"}, headers=_auth(token)
    )
    assert missing.json()["total"] == 0


async def test_catalog_out_of_stock_filter_excludes_unknown_and_preorder(client, db_session):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, refs["tier_copy"], "copy", "Display")
    store = await _make_store(db_session, "store-a")
    for index, status in enumerate(["out", "preorder", "unknown", "low", "in_stock"]):
        await _make_offer(
            db_session, store, product, str(index), str(index * 100), stock_status=status
        )
    response = await client.get("/api/products/catalog?in_stock=false", headers=_auth(token))
    item = response.json()["results"][0]
    assert item["offers_count"] == 1
    assert item["min_price_retail"] == "0.00"


@pytest.mark.parametrize(
    "params",
    [
        {"min_price": "-1"},
        {"max_price": "-1"},
        {"min_price": "NaN"},
        {"max_price": "Infinity"},
        {"min_price": "-Infinity"},
        {"max_price": "bad"},
        {"min_price": "2", "max_price": "1"},
        {"in_stock": "bad"},
    ],
)
async def test_catalog_rejects_invalid_offer_filters(client, db_session, params):
    _, token = await _make_user(db_session)
    response = await client.get("/api/products/catalog", params=params, headers=_auth(token))
    assert response.status_code == 422, response.text


@pytest.mark.parametrize("plan", [PlanEnum.trial, PlanEnum.basic, PlanEnum.advanced])
async def test_catalog_and_suggestions_gate_fuzzy_and_preserve_models(client, db_session, plan):
    from sqlalchemy import update

    user, token = await _make_user(db_session)
    await db_session.execute(
        update(Subscription).where(Subscription.user_id == user.id).values(plan=plan)
    )
    refs = await _make_dictionaries(db_session)
    store = await _make_store(db_session, "search-store")
    names = [
        "Дисплей iPhone 13",
        "Дисплей iPhone 12",
        "Nokia",
        "Samsung Galaxy A53",
        "Samsung Galaxy A52",
        "Дисплей Samsung Galaxy S22 Ultra",
    ]
    products = []
    for i, name in enumerate(names):
        product = await _make_product(db_session, refs, refs["tier_copy"], str(i), name)
        products.append(product)
        await _make_offer(db_session, store, product, str(i), "100")
    queries = [
        ("Nokia", [products[2].id]),
        ("iphone13", [products[0].id]),
        ("a53", [products[3].id]),
        ("dsiplay iphone13", [products[0].id]),
        ("экран Самсунг Галакси С22", [products[5].id]),
        ("Nokai", [products[2].id]),
        ("dsplay iphone13", [products[0].id]),
        ("экран самсунк галакси С22", [products[5].id]),
        ("шзрщту 13", [products[0].id]),
    ]
    for query, expected in queries:
        fuzzy_query = query in {
            "dsiplay iphone13",
            "экран Самсунг Галакси С22",
            "Nokai",
            "dsplay iphone13",
            "экран самсунк галакси С22",
            "шзрщту 13",
        }
        expected = expected if not fuzzy_query or plan == PlanEnum.advanced else []
        for path in ["/api/products/catalog", "/api/products/catalog/suggestions"]:
            response = await client.get(path, params={"q": query}, headers=_auth(token))
            assert response.status_code == 200, response.text
            body = response.json()
            rows = body["results"] if isinstance(body, dict) else body
            assert [row["id"] for row in rows] == expected, (plan, query, path, body)


async def test_suggestions_filters_require_active_matching_offers_and_bound_limit(
    client, db_session
):
    _, token = await _make_user(db_session)
    refs = await _make_dictionaries(db_session)
    store = await _make_store(db_session, "selected")
    other = await _make_store(db_session, "other")
    for index in range(10):
        product = await _make_product(
            db_session, refs, refs["tier_copy"], str(index), f"Nokia {index}"
        )
        await _make_offer(db_session, store, product, str(index), "100", stock_status="low")
    excluded = await _make_product(db_session, refs, refs["tier_copy"], "bad", "Nokia excluded")
    await _make_offer(db_session, store, excluded, "bad1", "900")
    await _make_offer(db_session, other, excluded, "bad2", "100")
    empty = await _make_product(db_session, refs, refs["tier_copy"], "empty", "Nokia empty")
    inactive = await _make_product(
        db_session, refs, refs["tier_copy"], "inactive", "Nokia inactive"
    )
    await _make_offer(db_session, store, inactive, "inactive", "100", is_active=False)
    response = await client.get(
        "/api/products/catalog/suggestions",
        headers=_auth(token),
        params={
            "q": "Nokia",
            "store": "selected",
            "min_price": "100",
            "max_price": "100",
            "in_stock": "true",
            "limit": 8,
            "device_id": refs["device"].id,
        },
    )
    assert response.status_code == 200, response.text
    assert len(response.json()) == 8
    assert all(set(row) == {"id", "canonical_name"} for row in response.json())
    assert not {excluded.id, empty.id, inactive.id} & {row["id"] for row in response.json()}
    for params in [
        {"q": "n"},
        {"q": "Nokia", "limit": 9},
        {"q": "Nokia", "min_price": 2, "max_price": 1},
    ]:
        response = await client.get(
            "/api/products/catalog/suggestions", params=params, headers=_auth(token)
        )
        assert response.status_code == 422


async def test_suggestions_reject_expired_subscription_and_anonymous(client, db_session):
    from sqlalchemy import update

    user, token = await _make_user(db_session)
    await db_session.execute(
        update(Subscription)
        .where(Subscription.user_id == user.id)
        .values(end_date=datetime.now(timezone.utc) - timedelta(days=1))
    )
    for headers in [{}, _auth(token)]:
        response = await client.get("/api/products/catalog/suggestions?q=Nokia", headers=headers)
        assert response.status_code == 403
