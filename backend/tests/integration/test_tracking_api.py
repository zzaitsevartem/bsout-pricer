from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from src.main import app
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.catalog.model.catalog import Brand, Device, PartType, QualityTier
from src.modules.products.model.product import Cluster, Product, StoreOffer
from src.modules.stores.model.store import Store
from src.modules.tracking.controller import tracking_router
from src.modules.tracking.model.tracking import TrackedProduct

pytestmark = pytest.mark.integration

if not any(getattr(route, "path", "").startswith("/api/tracking") for route in app.router.routes):
    app.include_router(tracking_router)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(
    db,
    email: str,
    plan: PlanEnum | None = PlanEnum.trial,
    ends_in_days: int = 7,
) -> tuple[User, str]:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Tracking User",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    if plan is not None:
        now = datetime.now(timezone.utc)
        db.add(
            Subscription(
                user_id=user.id,
                plan=plan,
                start_date=now,
                end_date=now + timedelta(days=ends_in_days),
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

    tier = QualityTier(code="copy", name_ru="Копия", rank=10)
    db.add(tier)
    await db.flush()

    cluster = Cluster(device_id=device.id, part_type_id=part_type.id, offers_count=0)
    db.add(cluster)
    await db.flush()

    return {"brand": brand, "cluster": cluster, "tier": tier}


async def _make_product(db, refs: dict, suffix: str, name: str | None = None) -> Product:
    product = Product(
        cluster_id=refs["cluster"].id,
        quality_tier_id=refs["tier"].id,
        brand_id=refs["brand"].id,
        canonical_key=f"apple-iphone-13|display|{suffix}",
        canonical_name=name or f"Дисплей iPhone 13 {suffix}",
    )
    db.add(product)
    await db.flush()
    return product


async def _make_products(db, refs: dict, count: int, prefix: str) -> list[Product]:
    products = [
        Product(
            cluster_id=refs["cluster"].id,
            quality_tier_id=refs["tier"].id,
            brand_id=refs["brand"].id,
            canonical_key=f"apple-iphone-13|display|{prefix}-{index}",
            canonical_name=f"Дисплей iPhone 13 {prefix}-{index}",
        )
        for index in range(count)
    ]
    db.add_all(products)
    await db.flush()
    return products


async def _make_store(db, slug: str) -> Store:
    store = Store(
        name=slug.upper(), slug=slug, website_url=f"http://{slug}.example.com", is_active=True
    )
    db.add(store)
    await db.flush()
    return store


async def _make_offer(db, store: Store, product: Product, sku: str, price: str) -> StoreOffer:
    offer = StoreOffer(
        store_id=store.id,
        product_id=product.id,
        source_sku=sku,
        title=f"Offer {sku}",
        normalized_title=f"offer {sku}",
        price_retail=Decimal(price),
        stock_status="in_stock",
        url=f"http://{store.slug}.example.com/{sku}",
        is_active=True,
        match_status="auto",
    )
    db.add(offer)
    await db.flush()
    return offer


async def _seed_tracked(db, user_id: int, products: list[Product], is_active: bool = True) -> None:
    db.add_all(
        [
            TrackedProduct(
                user_id=user_id,
                product_id=product.id,
                is_active=is_active,
                notify_on_any_drop=True,
            )
            for product in products
        ]
    )
    await db.flush()


async def test_tracking_requires_authentication(client):
    assert (await client.get("/api/tracking")).status_code == 403
    assert (await client.get("/api/tracking/usage")).status_code == 403
    assert (await client.post("/api/tracking", json={"productId": 1})).status_code == 403


async def test_tracking_forbidden_without_active_subscription(client, db_session):
    _, token = await _make_user(db_session, "track-nosub@example.com", plan=None)

    listed = await client.get("/api/tracking", headers=_auth(token))
    created = await client.post("/api/tracking", json={"productId": 1}, headers=_auth(token))

    assert listed.status_code == 403, listed.text
    assert created.status_code == 403, created.text
    assert created.json()["detail"]["code"] == "subscription_required"


async def test_usage_stays_readable_without_subscription_for_upsell(client, db_session):
    _, token = await _make_user(db_session, "track-usage-nosub@example.com", plan=None)

    usage = await client.get("/api/tracking/usage", headers=_auth(token))

    assert usage.status_code == 200, usage.text
    body = usage.json()
    assert body["used"] == 0
    assert body["limit"] == 0
    assert body["plan"] is None


async def test_create_tracking_fills_last_seen_price_from_city_minimum(client, db_session):
    _, token = await _make_user(db_session, "track-create@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")

    store_a = await _make_store(db_session, "store-a")
    store_b = await _make_store(db_session, "store-b")
    await _make_offer(db_session, store_a, product, "A1", "5000.00")
    await _make_offer(db_session, store_b, product, "B1", "4200.00")

    resp = await client.post(
        "/api/tracking",
        json={"productId": product.id, "targetPrice": "4000.00"},
        headers=_auth(token),
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["product_id"] == product.id
    assert body["canonical_name"] == "Дисплей iPhone 13 copy"
    assert body["last_seen_price"] == "4200.00"
    assert body["current_price"] == "4200.00"
    assert body["price_delta"] == "0.00"
    assert body["target_price"] == "4000.00"
    assert body["stores_count"] == 2
    assert body["is_active"] is True
    assert body["notify_on_any_drop"] is True
    assert body["target_reached"] is False

    stored = (
        await db_session.execute(select(TrackedProduct).where(TrackedProduct.id == body["id"]))
    ).scalar_one()
    assert stored.last_seen_price == Decimal("4200.00")


async def test_create_tracking_accepts_snake_case_body(client, db_session):
    _, token = await _make_user(db_session, "track-snake@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")

    resp = await client.post(
        "/api/tracking",
        json={"product_id": product.id, "target_price": "1500.00"},
        headers=_auth(token),
    )

    assert resp.status_code == 201, resp.text
    assert resp.json()["target_price"] == "1500.00"


async def test_create_tracking_without_offers_leaves_last_seen_price_null(client, db_session):
    _, token = await _make_user(db_session, "track-nooffers@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")

    resp = await client.post("/api/tracking", json={"productId": product.id}, headers=_auth(token))

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["last_seen_price"] is None
    assert body["current_price"] is None
    assert body["price_delta"] is None
    assert body["stores_count"] == 0


async def test_create_tracking_unknown_product_returns_404(client, db_session):
    _, token = await _make_user(db_session, "track-404@example.com")

    resp = await client.post("/api/tracking", json={"productId": 424242}, headers=_auth(token))

    assert resp.status_code == 404, resp.text
    assert resp.json()["detail"] == "Canonical product not found"


async def test_repeated_create_is_idempotent_and_does_not_duplicate(client, db_session):
    user, token = await _make_user(db_session, "track-idem@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")
    store = await _make_store(db_session, "store-a")
    await _make_offer(db_session, store, product, "A1", "3000.00")

    first = await client.post("/api/tracking", json={"productId": product.id}, headers=_auth(token))
    second = await client.post(
        "/api/tracking",
        json={"productId": product.id, "targetPrice": "2500.00"},
        headers=_auth(token),
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 200, second.text
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["target_price"] == "2500.00"

    rows = (
        (await db_session.execute(select(TrackedProduct).where(TrackedProduct.user_id == user.id)))
        .scalars()
        .all()
    )
    assert len(rows) == 1


async def test_trial_plan_blocks_eleventh_tracked_product(client, db_session):
    _, token = await _make_user(db_session, "track-trial-limit@example.com", plan=PlanEnum.trial)
    refs = await _make_dictionaries(db_session)
    products = await _make_products(db_session, refs, 11, "trial")

    for product in products[:10]:
        created = await client.post(
            "/api/tracking", json={"productId": product.id}, headers=_auth(token)
        )
        assert created.status_code == 201, created.text

    blocked = await client.post(
        "/api/tracking", json={"productId": products[10].id}, headers=_auth(token)
    )

    assert blocked.status_code == 402, blocked.text
    detail = blocked.json()["detail"]
    assert detail["code"] == "tracking_limit_reached"
    assert detail["limit"] == 10
    assert detail["used"] == 10
    assert detail["plan"] == "trial"
    assert "10" in detail["message"]


async def test_advanced_plan_allows_500_tracked_products(client, db_session):
    user, token = await _make_user(
        db_session, "track-adv-limit@example.com", plan=PlanEnum.advanced, ends_in_days=30
    )
    refs = await _make_dictionaries(db_session)
    products = await _make_products(db_session, refs, 501, "adv")

    await _seed_tracked(db_session, user.id, products[:499])

    five_hundredth = await client.post(
        "/api/tracking", json={"productId": products[499].id}, headers=_auth(token)
    )
    over_limit = await client.post(
        "/api/tracking", json={"productId": products[500].id}, headers=_auth(token)
    )

    assert five_hundredth.status_code == 201, five_hundredth.text
    assert over_limit.status_code == 402, over_limit.text
    detail = over_limit.json()["detail"]
    assert detail["code"] == "tracking_limit_reached"
    assert detail["limit"] == 500
    assert detail["used"] == 500
    assert detail["plan"] == "advanced"


async def test_list_returns_only_own_tracked_products(client, db_session):
    owner, owner_token = await _make_user(db_session, "track-owner@example.com")
    stranger, _ = await _make_user(db_session, "track-stranger@example.com")
    refs = await _make_dictionaries(db_session)
    mine = await _make_product(db_session, refs, "mine")
    theirs = await _make_product(db_session, refs, "theirs")

    await _seed_tracked(db_session, owner.id, [mine])
    await _seed_tracked(db_session, stranger.id, [theirs])

    resp = await client.get("/api/tracking", headers=_auth(owner_token))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert [item["product_id"] for item in body["results"]] == [mine.id]


async def test_list_reports_current_price_stores_count_and_delta(client, db_session):
    _, token = await _make_user(db_session, "track-delta@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")

    store_a = await _make_store(db_session, "store-a")
    store_b = await _make_store(db_session, "store-b")
    await _make_offer(db_session, store_a, product, "A1", "5000.00")
    offer_b = await _make_offer(db_session, store_b, product, "B1", "4200.00")

    created = await client.post(
        "/api/tracking",
        json={"productId": product.id, "targetPrice": "3900.00"},
        headers=_auth(token),
    )
    assert created.status_code == 201, created.text

    offer_b.price_retail = Decimal("3800.00")
    await db_session.flush()

    resp = await client.get("/api/tracking", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["per_page"] == 20
    item = body["results"][0]
    assert item["last_seen_price"] == "4200.00"
    assert item["current_price"] == "3800.00"
    assert item["price_delta"] == "-400.00"
    assert item["price_delta_pct"] == pytest.approx(-9.52)
    assert item["stores_count"] == 2
    assert item["target_reached"] is True


async def test_list_pagination_and_active_filter(client, db_session):
    user, token = await _make_user(db_session, "track-page@example.com")
    refs = await _make_dictionaries(db_session)
    products = await _make_products(db_session, refs, 3, "page")

    await _seed_tracked(db_session, user.id, products[:2], is_active=True)
    await _seed_tracked(db_session, user.id, products[2:], is_active=False)

    page_one = await client.get("/api/tracking?per_page=2&page=1", headers=_auth(token))
    page_two = await client.get("/api/tracking?per_page=2&page=2", headers=_auth(token))
    only_active = await client.get("/api/tracking?is_active=true", headers=_auth(token))

    assert page_one.json()["total"] == 3
    assert len(page_one.json()["results"]) == 2
    assert len(page_two.json()["results"]) == 1
    assert only_active.json()["total"] == 2
    assert all(item["is_active"] for item in only_active.json()["results"])


async def test_usage_counts_only_active_tracked_products(client, db_session):
    user, token = await _make_user(db_session, "track-usage@example.com", plan=PlanEnum.trial)
    refs = await _make_dictionaries(db_session)
    products = await _make_products(db_session, refs, 3, "usage")

    await _seed_tracked(db_session, user.id, products[:2], is_active=True)
    await _seed_tracked(db_session, user.id, products[2:], is_active=False)

    resp = await client.get("/api/tracking/usage", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"used": 2, "limit": 10, "remaining": 8, "plan": "trial"}


async def test_usage_reflects_plan_limit(client, db_session):
    user, token = await _make_user(
        db_session, "track-usage-basic@example.com", plan=PlanEnum.basic, ends_in_days=30
    )
    refs = await _make_dictionaries(db_session)
    products = await _make_products(db_session, refs, 1, "basic")
    await _seed_tracked(db_session, user.id, products)

    resp = await client.get("/api/tracking/usage", headers=_auth(token))

    assert resp.json() == {"used": 1, "limit": 100, "remaining": 99, "plan": "basic"}


async def test_patch_updates_target_price_and_flags(client, db_session):
    user, token = await _make_user(db_session, "track-patch@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")
    await _seed_tracked(db_session, user.id, [product])

    tracked = (
        await db_session.execute(select(TrackedProduct).where(TrackedProduct.user_id == user.id))
    ).scalar_one()

    resp = await client.patch(
        f"/api/tracking/{tracked.id}",
        json={"targetPrice": "1234.00", "notifyOnAnyDrop": False, "isActive": False},
        headers=_auth(token),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["target_price"] == "1234.00"
    assert body["notify_on_any_drop"] is False
    assert body["is_active"] is False

    await db_session.refresh(tracked)
    assert tracked.target_price == Decimal("1234.00")
    assert tracked.is_active is False


async def test_patch_partial_body_leaves_other_fields_untouched(client, db_session):
    user, token = await _make_user(db_session, "track-patch-partial@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")
    db_session.add(
        TrackedProduct(
            user_id=user.id,
            product_id=product.id,
            target_price=Decimal("999.00"),
            notify_on_any_drop=True,
            is_active=True,
        )
    )
    await db_session.flush()
    tracked = (
        await db_session.execute(select(TrackedProduct).where(TrackedProduct.user_id == user.id))
    ).scalar_one()

    resp = await client.patch(
        f"/api/tracking/{tracked.id}", json={"notifyOnAnyDrop": False}, headers=_auth(token)
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["target_price"] == "999.00"
    assert resp.json()["notify_on_any_drop"] is False
    assert resp.json()["is_active"] is True


async def test_patch_foreign_tracked_product_returns_404(client, db_session):
    owner, _ = await _make_user(db_session, "track-patch-owner@example.com")
    _, stranger_token = await _make_user(db_session, "track-patch-stranger@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")
    await _seed_tracked(db_session, owner.id, [product])

    tracked = (
        await db_session.execute(select(TrackedProduct).where(TrackedProduct.user_id == owner.id))
    ).scalar_one()

    resp = await client.patch(
        f"/api/tracking/{tracked.id}",
        json={"targetPrice": "1.00"},
        headers=_auth(stranger_token),
    )

    assert resp.status_code == 404, resp.text
    assert resp.json()["detail"] == "Tracked product not found"

    await db_session.refresh(tracked)
    assert tracked.target_price is None


async def test_patch_reactivation_over_limit_is_blocked(client, db_session):
    user, token = await _make_user(db_session, "track-reactivate@example.com")
    refs = await _make_dictionaries(db_session)
    products = await _make_products(db_session, refs, 11, "react")

    await _seed_tracked(db_session, user.id, products[:10], is_active=True)
    await _seed_tracked(db_session, user.id, products[10:], is_active=False)

    inactive = (
        await db_session.execute(
            select(TrackedProduct)
            .where(TrackedProduct.user_id == user.id)
            .where(TrackedProduct.is_active.is_(False))
        )
    ).scalar_one()

    resp = await client.patch(
        f"/api/tracking/{inactive.id}", json={"isActive": True}, headers=_auth(token)
    )

    assert resp.status_code == 402, resp.text
    assert resp.json()["detail"]["code"] == "tracking_limit_reached"
    assert resp.json()["detail"]["used"] == 10


async def test_delete_removes_tracked_product(client, db_session):
    user, token = await _make_user(db_session, "track-delete@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")
    await _seed_tracked(db_session, user.id, [product])

    tracked = (
        await db_session.execute(select(TrackedProduct).where(TrackedProduct.user_id == user.id))
    ).scalar_one()

    resp = await client.delete(f"/api/tracking/{tracked.id}", headers=_auth(token))

    assert resp.status_code == 204, resp.text
    remaining = (
        (await db_session.execute(select(TrackedProduct).where(TrackedProduct.user_id == user.id)))
        .scalars()
        .all()
    )
    assert remaining == []


async def test_delete_frees_a_slot_for_the_plan_limit(client, db_session):
    user, token = await _make_user(db_session, "track-delete-slot@example.com")
    refs = await _make_dictionaries(db_session)
    products = await _make_products(db_session, refs, 11, "slot")
    await _seed_tracked(db_session, user.id, products[:10])

    blocked = await client.post(
        "/api/tracking", json={"productId": products[10].id}, headers=_auth(token)
    )
    assert blocked.status_code == 402, blocked.text

    tracked = (
        await db_session.execute(
            select(TrackedProduct).where(TrackedProduct.user_id == user.id).limit(1)
        )
    ).scalar_one()
    removed = await client.delete(f"/api/tracking/{tracked.id}", headers=_auth(token))
    assert removed.status_code == 204, removed.text

    retried = await client.post(
        "/api/tracking", json={"productId": products[10].id}, headers=_auth(token)
    )

    assert retried.status_code == 201, retried.text


async def test_delete_foreign_tracked_product_returns_404(client, db_session):
    owner, _ = await _make_user(db_session, "track-del-owner@example.com")
    _, stranger_token = await _make_user(db_session, "track-del-stranger@example.com")
    refs = await _make_dictionaries(db_session)
    product = await _make_product(db_session, refs, "copy")
    await _seed_tracked(db_session, owner.id, [product])

    tracked = (
        await db_session.execute(select(TrackedProduct).where(TrackedProduct.user_id == owner.id))
    ).scalar_one()

    resp = await client.delete(f"/api/tracking/{tracked.id}", headers=_auth(stranger_token))

    assert resp.status_code == 404, resp.text
    survivors = (
        (await db_session.execute(select(TrackedProduct).where(TrackedProduct.user_id == owner.id)))
        .scalars()
        .all()
    )
    assert len(survivors) == 1


async def test_deactivated_tracking_frees_usage_counter(client, db_session):
    user, token = await _make_user(db_session, "track-usage-free@example.com")
    refs = await _make_dictionaries(db_session)
    products = await _make_products(db_session, refs, 2, "free")
    await _seed_tracked(db_session, user.id, products)

    tracked = (
        await db_session.execute(
            select(TrackedProduct).where(TrackedProduct.user_id == user.id).limit(1)
        )
    ).scalar_one()

    before = await client.get("/api/tracking/usage", headers=_auth(token))
    await client.patch(
        f"/api/tracking/{tracked.id}", json={"isActive": False}, headers=_auth(token)
    )
    after = await client.get("/api/tracking/usage", headers=_auth(token))

    assert before.json()["used"] == 2
    assert after.json()["used"] == 1
    assert after.json()["remaining"] == 9
