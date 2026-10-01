from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.products.model.product import Product, StoreOffer
from src.modules.stores.model.store import Store
from src.modules.tracking.model.tracking import Notification, TrackedProduct
from src.modules.tracking.service.alert_service import AlertService

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def notifications_app():
    from src.main import app
    from src.modules.tracking.controller.notifications import notifications_router

    paths = {getattr(route, "path", None) for route in app.routes}
    if "/api/notifications" not in paths:
        app.include_router(notifications_router)
    return app


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(db, email: str, plan: PlanEnum | None = PlanEnum.advanced) -> tuple[User, str]:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Alert User",
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
                end_date=now + timedelta(days=30),
                is_active=True,
            )
        )
        await db.flush()

    return user, create_access_token(user.id)


async def _make_product(db, suffix: str, name: str = "Дисплей iPhone 13") -> Product:
    product = Product(canonical_key=f"alerts-{suffix}", canonical_name=f"{name} {suffix}")
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
    product: Product,
    sku: str,
    price: str,
    is_active: bool = True,
) -> StoreOffer:
    offer = StoreOffer(
        store_id=store.id,
        product_id=product.id,
        source_sku=sku,
        title=f"Offer {sku}",
        normalized_title=f"offer {sku}",
        price_retail=Decimal(price),
        stock_status="in_stock",
        url=f"http://{store.slug}.example.com/{sku}",
        is_active=is_active,
        match_status="auto",
    )
    db.add(offer)
    await db.flush()
    return offer


async def _track(
    db,
    user: User,
    product: Product,
    last_seen_price: str | None = None,
    target_price: str | None = None,
    notify_on_any_drop: bool = True,
    is_active: bool = True,
) -> TrackedProduct:
    tracked = TrackedProduct(
        user_id=user.id,
        product_id=product.id,
        target_price=Decimal(target_price) if target_price else None,
        notify_on_any_drop=notify_on_any_drop,
        last_seen_price=Decimal(last_seen_price) if last_seen_price else None,
        is_active=is_active,
    )
    db.add(tracked)
    await db.flush()
    return tracked


async def _set_price(db, offer: StoreOffer, price: str) -> None:
    offer.price_retail = Decimal(price)
    await db.flush()


async def _count_notifications(db, user_id: int | None = None) -> int:
    stmt = select(func.count(Notification.id))
    if user_id is not None:
        stmt = stmt.where(Notification.user_id == user_id)
    return (await db.execute(stmt)).scalar() or 0


async def _make_notification(
    db,
    user: User,
    product: Product,
    dedup_key: str,
    read: bool = False,
    notification_type: str = "price_drop",
) -> Notification:
    notification = Notification(
        user_id=user.id,
        product_id=product.id,
        type=notification_type,
        channel="in_app",
        status="sent",
        title="Цена снизилась",
        body="Тестовое уведомление",
        old_price=Decimal("2000.00"),
        new_price=Decimal("1500.00"),
        dedup_key=dedup_key,
        read_at=datetime.now(timezone.utc) if read else None,
    )
    db.add(notification)
    await db.flush()
    return notification


async def test_price_drop_creates_notification_once(db_session):
    user, _ = await _make_user(db_session, "drop@example.com")
    product = await _make_product(db_session, "drop")
    store = await _make_store(db_session, "store-drop")
    offer = await _make_offer(db_session, store, product, "sku-drop", "2000.00")
    tracked = await _track(db_session, user, product, last_seen_price="2000.00")

    await _set_price(db_session, offer, "1500.00")
    created = await AlertService.scan_for_drops(db_session)

    assert len(created) == 1
    notification = created[0]
    assert notification.type == "price_drop"
    assert notification.user_id == user.id
    assert notification.tracked_product_id == tracked.id
    assert notification.product_id == product.id
    assert notification.old_price == Decimal("2000.00")
    assert notification.new_price == Decimal("1500.00")
    assert notification.status == "sent"
    assert notification.sent_at is not None
    assert tracked.last_seen_price == Decimal("1500.00")
    assert tracked.last_notified_at is not None

    assert await AlertService.scan_for_drops(db_session) == []
    assert await _count_notifications(db_session, user.id) == 1


async def test_repeated_scan_of_same_drop_is_deduplicated(db_session):
    user, _ = await _make_user(db_session, "dedup@example.com")
    product = await _make_product(db_session, "dedup")
    store = await _make_store(db_session, "store-dedup")
    offer = await _make_offer(db_session, store, product, "sku-dedup", "2000.00")
    tracked = await _track(db_session, user, product, last_seen_price="2000.00")

    await _set_price(db_session, offer, "1500.00")
    assert len(await AlertService.scan_for_drops(db_session)) == 1

    tracked.last_seen_price = Decimal("2000.00")
    await db_session.flush()

    assert await AlertService.scan_for_drops(db_session) == []
    assert await _count_notifications(db_session, user.id) == 1
    assert tracked.last_seen_price == Decimal("1500.00")


async def test_dedup_key_distinguishes_different_prices(db_session):
    user, _ = await _make_user(db_session, "dedup-prices@example.com")
    product = await _make_product(db_session, "dedup-prices")
    store = await _make_store(db_session, "store-dedup-prices")
    offer = await _make_offer(db_session, store, product, "sku-dedup-prices", "2000.00")
    await _track(db_session, user, product, last_seen_price="2000.00")

    await _set_price(db_session, offer, "1500.00")
    first = await AlertService.scan_for_drops(db_session)

    await _set_price(db_session, offer, "1400.00")
    second = await AlertService.scan_for_drops(db_session)

    assert len(first) == 1
    assert len(second) == 1
    assert first[0].dedup_key != second[0].dedup_key
    assert second[0].old_price == Decimal("1500.00")
    assert second[0].new_price == Decimal("1400.00")
    assert await _count_notifications(db_session, user.id) == 2


async def test_price_increase_creates_no_notification_but_updates_last_seen(db_session):
    user, _ = await _make_user(db_session, "increase@example.com")
    product = await _make_product(db_session, "increase")
    store = await _make_store(db_session, "store-increase")
    offer = await _make_offer(db_session, store, product, "sku-increase", "1500.00")
    tracked = await _track(db_session, user, product, last_seen_price="1500.00")

    await _set_price(db_session, offer, "1800.00")

    assert await AlertService.scan_for_drops(db_session) == []
    assert tracked.last_seen_price == Decimal("1800.00")
    assert tracked.last_notified_at is None
    assert await _count_notifications(db_session, user.id) == 0


async def test_return_to_previous_level_after_increase_is_a_real_drop(db_session):
    user, _ = await _make_user(db_session, "rebound@example.com")
    product = await _make_product(db_session, "rebound")
    store = await _make_store(db_session, "store-rebound")
    offer = await _make_offer(db_session, store, product, "sku-rebound", "1500.00")
    tracked = await _track(db_session, user, product, last_seen_price="1500.00")

    await _set_price(db_session, offer, "1800.00")
    assert await AlertService.scan_for_drops(db_session) == []

    await _set_price(db_session, offer, "1500.00")
    created = await AlertService.scan_for_drops(db_session)

    assert len(created) == 1
    assert created[0].old_price == Decimal("1800.00")
    assert created[0].new_price == Decimal("1500.00")
    assert tracked.last_seen_price == Decimal("1500.00")


async def test_target_reached_wins_over_price_drop(db_session):
    user, _ = await _make_user(db_session, "target@example.com")
    product = await _make_product(db_session, "target")
    store = await _make_store(db_session, "store-target")
    offer = await _make_offer(db_session, store, product, "sku-target", "2000.00")
    await _track(db_session, user, product, last_seen_price="2000.00", target_price="1600.00")

    await _set_price(db_session, offer, "1500.00")
    created = await AlertService.scan_for_drops(db_session)

    assert len(created) == 1
    assert created[0].type == "target_reached"
    assert created[0].dedup_key.endswith(":target_reached:1500.00")


async def test_drop_above_target_is_a_plain_price_drop(db_session):
    user, _ = await _make_user(db_session, "above-target@example.com")
    product = await _make_product(db_session, "above-target")
    store = await _make_store(db_session, "store-above-target")
    offer = await _make_offer(db_session, store, product, "sku-above-target", "2000.00")
    await _track(db_session, user, product, last_seen_price="2000.00", target_price="1000.00")

    await _set_price(db_session, offer, "1700.00")
    created = await AlertService.scan_for_drops(db_session)

    assert len(created) == 1
    assert created[0].type == "price_drop"


async def test_notify_on_any_drop_disabled_only_reacts_to_target(db_session):
    user, _ = await _make_user(db_session, "any-drop-off@example.com")
    product = await _make_product(db_session, "any-drop-off")
    store = await _make_store(db_session, "store-any-drop-off")
    offer = await _make_offer(db_session, store, product, "sku-any-drop-off", "2000.00")
    tracked = await _track(
        db_session,
        user,
        product,
        last_seen_price="2000.00",
        target_price="1200.00",
        notify_on_any_drop=False,
    )

    await _set_price(db_session, offer, "1500.00")
    assert await AlertService.scan_for_drops(db_session) == []
    assert tracked.last_seen_price == Decimal("1500.00")

    await _set_price(db_session, offer, "1100.00")
    created = await AlertService.scan_for_drops(db_session)

    assert len(created) == 1
    assert created[0].type == "target_reached"


@pytest.mark.parametrize("plan", [PlanEnum.trial, PlanEnum.basic, None])
async def test_plans_without_price_alerts_get_no_notifications(db_session, plan):
    label = plan.value if plan else "nosub"
    user, _ = await _make_user(db_session, f"gated-{label}@example.com", plan=plan)
    product = await _make_product(db_session, f"gated-{label}")
    store = await _make_store(db_session, f"store-gated-{label}")
    offer = await _make_offer(db_session, store, product, f"sku-gated-{label}", "2000.00")
    tracked = await _track(db_session, user, product, last_seen_price="2000.00")

    await _set_price(db_session, offer, "1500.00")

    assert await AlertService.scan_for_drops(db_session) == []
    assert await _count_notifications(db_session, user.id) == 0
    assert tracked.last_seen_price == Decimal("1500.00")
    assert tracked.last_notified_at is None


async def test_only_advanced_user_is_notified_for_shared_product(db_session):
    advanced, _ = await _make_user(db_session, "shared-advanced@example.com")
    basic, _ = await _make_user(db_session, "shared-basic@example.com", plan=PlanEnum.basic)
    product = await _make_product(db_session, "shared")
    store = await _make_store(db_session, "store-shared")
    offer = await _make_offer(db_session, store, product, "sku-shared", "2000.00")
    advanced_tracked = await _track(db_session, advanced, product, last_seen_price="2000.00")
    basic_tracked = await _track(db_session, basic, product, last_seen_price="2000.00")

    await _set_price(db_session, offer, "1500.00")
    created = await AlertService.scan_for_drops(db_session)

    assert len(created) == 1
    assert created[0].user_id == advanced.id
    assert advanced_tracked.last_seen_price == Decimal("1500.00")
    assert basic_tracked.last_seen_price == Decimal("1500.00")
    assert await _count_notifications(db_session, basic.id) == 0


async def test_scan_uses_cheapest_active_offer_only(db_session):
    user, _ = await _make_user(db_session, "cheapest@example.com")
    product = await _make_product(db_session, "cheapest")
    store_a = await _make_store(db_session, "store-cheapest-a")
    store_b = await _make_store(db_session, "store-cheapest-b")
    await _make_offer(db_session, store_a, product, "sku-cheapest-a", "1900.00")
    await _make_offer(db_session, store_b, product, "sku-cheapest-b", "1200.00", is_active=False)
    tracked = await _track(db_session, user, product, last_seen_price="2000.00")

    created = await AlertService.scan_for_drops(db_session)

    assert len(created) == 1
    assert created[0].new_price == Decimal("1900.00")
    assert tracked.last_seen_price == Decimal("1900.00")


async def test_product_without_active_offers_is_skipped(db_session):
    user, _ = await _make_user(db_session, "no-offers@example.com")
    product = await _make_product(db_session, "no-offers")
    store = await _make_store(db_session, "store-no-offers")
    await _make_offer(db_session, store, product, "sku-no-offers", "1000.00", is_active=False)
    tracked = await _track(db_session, user, product, last_seen_price="2000.00")

    assert await AlertService.scan_for_drops(db_session) == []
    assert tracked.last_seen_price == Decimal("2000.00")


async def test_inactive_tracking_is_ignored(db_session):
    user, _ = await _make_user(db_session, "inactive@example.com")
    product = await _make_product(db_session, "inactive")
    store = await _make_store(db_session, "store-inactive")
    offer = await _make_offer(db_session, store, product, "sku-inactive", "2000.00")
    tracked = await _track(db_session, user, product, last_seen_price="2000.00", is_active=False)

    await _set_price(db_session, offer, "1500.00")

    assert await AlertService.scan_for_drops(db_session) == []
    assert tracked.last_seen_price == Decimal("2000.00")


async def test_scan_can_be_narrowed_to_product_ids(db_session):
    user, _ = await _make_user(db_session, "narrow@example.com")
    first = await _make_product(db_session, "narrow-1")
    second = await _make_product(db_session, "narrow-2")
    store = await _make_store(db_session, "store-narrow")
    first_offer = await _make_offer(db_session, store, first, "sku-narrow-1", "2000.00")
    second_offer = await _make_offer(db_session, store, second, "sku-narrow-2", "2000.00")
    first_tracked = await _track(db_session, user, first, last_seen_price="2000.00")
    second_tracked = await _track(db_session, user, second, last_seen_price="2000.00")

    await _set_price(db_session, first_offer, "1500.00")
    await _set_price(db_session, second_offer, "1500.00")

    created = await AlertService.scan_for_drops(db_session, product_ids=[first.id])

    assert len(created) == 1
    assert created[0].product_id == first.id
    assert first_tracked.last_seen_price == Decimal("1500.00")
    assert second_tracked.last_seen_price == Decimal("2000.00")


async def test_empty_product_ids_scan_does_nothing(db_session):
    user, _ = await _make_user(db_session, "empty-scan@example.com")
    product = await _make_product(db_session, "empty-scan")
    store = await _make_store(db_session, "store-empty-scan")
    await _make_offer(db_session, store, product, "sku-empty-scan", "1000.00")
    tracked = await _track(db_session, user, product, last_seen_price="2000.00")

    assert await AlertService.scan_for_drops(db_session, product_ids=[]) == []
    assert tracked.last_seen_price == Decimal("2000.00")


async def test_first_scan_without_last_seen_price_only_reports_target(db_session):
    plain_user, _ = await _make_user(db_session, "first-plain@example.com")
    target_user, _ = await _make_user(db_session, "first-target@example.com")
    product = await _make_product(db_session, "first-scan")
    store = await _make_store(db_session, "store-first-scan")
    await _make_offer(db_session, store, product, "sku-first-scan", "1500.00")
    plain_tracked = await _track(db_session, plain_user, product)
    await _track(db_session, target_user, product, target_price="1600.00")

    created = await AlertService.scan_for_drops(db_session)

    assert len(created) == 1
    assert created[0].user_id == target_user.id
    assert created[0].type == "target_reached"
    assert created[0].old_price is None
    assert plain_tracked.last_seen_price == Decimal("1500.00")


async def test_notifications_endpoints_require_auth(client):
    assert (await client.get("/api/notifications")).status_code == 403
    assert (await client.get("/api/notifications/unread-count")).status_code == 403
    assert (await client.post("/api/notifications/1/read")).status_code == 403


async def test_list_returns_only_own_notifications(client, db_session):
    owner, owner_token = await _make_user(db_session, "list-owner@example.com")
    stranger, stranger_token = await _make_user(db_session, "list-stranger@example.com")
    product = await _make_product(db_session, "list")
    own = await _make_notification(db_session, owner, product, "own-1")
    await _make_notification(db_session, stranger, product, "stranger-1")

    resp = await client.get("/api/notifications", headers=_auth(owner_token))

    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["total"] == 1
    assert [item["id"] for item in payload["results"]] == [own.id]
    assert payload["results"][0]["type"] == "price_drop"
    assert payload["results"][0]["is_read"] is False
    assert payload["page"] == 1
    assert payload["per_page"] == 20

    stranger_resp = await client.get("/api/notifications", headers=_auth(stranger_token))
    assert [item["id"] for item in stranger_resp.json()["results"]] != [own.id]


async def test_unread_filter_and_unread_count(client, db_session):
    user, token = await _make_user(db_session, "unread@example.com")
    product = await _make_product(db_session, "unread")
    unread = await _make_notification(db_session, user, product, "unread-1")
    await _make_notification(db_session, user, product, "read-1", read=True)

    count = await client.get("/api/notifications/unread-count", headers=_auth(token))
    assert count.status_code == 200, count.text
    assert count.json() == {"unread_count": 1}

    only_unread = await client.get("/api/notifications?unread=true", headers=_auth(token))
    assert only_unread.json()["total"] == 1
    assert [item["id"] for item in only_unread.json()["results"]] == [unread.id]

    only_read = await client.get("/api/notifications?unread=false", headers=_auth(token))
    assert only_read.json()["total"] == 1
    assert only_read.json()["results"][0]["is_read"] is True

    everything = await client.get("/api/notifications", headers=_auth(token))
    assert everything.json()["total"] == 2


async def test_mark_read_updates_state_and_is_idempotent(client, db_session):
    user, token = await _make_user(db_session, "mark-read@example.com")
    product = await _make_product(db_session, "mark-read")
    notification = await _make_notification(db_session, user, product, "mark-read-1")

    first = await client.post(f"/api/notifications/{notification.id}/read", headers=_auth(token))
    assert first.status_code == 200, first.text
    assert first.json()["is_read"] is True
    assert first.json()["read_at"] is not None

    second = await client.post(f"/api/notifications/{notification.id}/read", headers=_auth(token))
    assert second.status_code == 200
    assert second.json()["read_at"] == first.json()["read_at"]

    count = await client.get("/api/notifications/unread-count", headers=_auth(token))
    assert count.json() == {"unread_count": 0}


async def test_marking_foreign_notification_returns_404(client, db_session):
    owner, _ = await _make_user(db_session, "foreign-owner@example.com")
    _, stranger_token = await _make_user(db_session, "foreign-stranger@example.com")
    product = await _make_product(db_session, "foreign")
    notification = await _make_notification(db_session, owner, product, "foreign-1")

    resp = await client.post(
        f"/api/notifications/{notification.id}/read", headers=_auth(stranger_token)
    )

    assert resp.status_code == 404, resp.text
    assert notification.read_at is None


async def test_missing_notification_returns_404(client, db_session):
    _, token = await _make_user(db_session, "missing@example.com")

    resp = await client.post("/api/notifications/999999/read", headers=_auth(token))

    assert resp.status_code == 404, resp.text


async def test_list_is_paginated_newest_first(client, db_session):
    user, token = await _make_user(db_session, "paging@example.com")
    product = await _make_product(db_session, "paging")
    created = [
        await _make_notification(db_session, user, product, f"paging-{index}") for index in range(3)
    ]

    first_page = await client.get("/api/notifications?page=1&per_page=2", headers=_auth(token))
    second_page = await client.get("/api/notifications?page=2&per_page=2", headers=_auth(token))

    assert first_page.json()["total"] == 3
    assert [item["id"] for item in first_page.json()["results"]] == [
        created[2].id,
        created[1].id,
    ]
    assert [item["id"] for item in second_page.json()["results"]] == [created[0].id]


async def test_scanned_notification_is_visible_through_api(client, db_session):
    user, token = await _make_user(db_session, "e2e@example.com")
    product = await _make_product(db_session, "e2e")
    store = await _make_store(db_session, "store-e2e")
    offer = await _make_offer(db_session, store, product, "sku-e2e", "2000.00")
    await _track(db_session, user, product, last_seen_price="2000.00")

    await _set_price(db_session, offer, "1500.00")
    await AlertService.scan_for_drops(db_session)

    resp = await client.get("/api/notifications?unread=true", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["total"] == 1
    item = payload["results"][0]
    assert item["type"] == "price_drop"
    assert item["status"] == "sent"
    assert item["old_price"] == "2000.00"
    assert item["new_price"] == "1500.00"
    assert product.canonical_name in item["title"]
