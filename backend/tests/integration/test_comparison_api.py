from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.modules.auth.model.user import User
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


def _reset_rate_limit() -> None:
    from src.main import app
    from src.middleware.rate_limit import RateLimitMiddleware

    if app.middleware_stack is None:
        app.middleware_stack = app.build_middleware_stack()

    node = app.middleware_stack
    while node is not None:
        if isinstance(node, RateLimitMiddleware):
            node._requests.clear()
            node._since_sweep = 0
            return
        node = getattr(node, "app", None)


@pytest.fixture(autouse=True)
def isolate_rate_limit():
    _reset_rate_limit()
    yield
    _reset_rate_limit()


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
