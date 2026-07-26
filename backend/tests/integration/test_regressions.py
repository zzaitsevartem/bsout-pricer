from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_access_token, create_refresh_token, hash_password
from src.modules.payment.service.payment_service import PaymentService
from src.modules.products.model.product import Product
from src.modules.products.service.comparison_service import ComparisonService

pytestmark = pytest.mark.integration

PASSWORD = "s3cret-pass"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(db_session, email: str) -> User:
    user = User(
        email=email,
        password_hash=hash_password(PASSWORD),
        full_name="Reg User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def _activate_subscription(db_session, user: User) -> Subscription:
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user.id,
        plan=PlanEnum.basic,
        start_date=now,
        end_date=now + timedelta(days=30),
        is_active=True,
    )
    db_session.add(subscription)
    await db_session.flush()
    return subscription


async def test_product_search_records_search_history(client, db_session):
    user = await _make_user(db_session, "history@example.com")
    await _activate_subscription(db_session, user)
    token = create_access_token(user.id)

    resp = await client.get("/api/products?q=дисплей+iphone", headers=_auth(token))
    assert resp.status_code == 200

    history = await client.get("/api/search/history", headers=_auth(token))
    assert history.status_code == 200

    entries = history.json()
    assert len(entries) == 1
    assert entries[0]["query"] == "дисплей iphone"
    assert entries[0]["results_count"] == resp.json()["total"]
    assert entries[0]["filters"]["fuzzy"] is False


async def test_blank_query_does_not_record_history(client, db_session):
    user = await _make_user(db_session, "blank@example.com")
    await _activate_subscription(db_session, user)
    token = create_access_token(user.id)

    assert (await client.get("/api/products", headers=_auth(token))).status_code == 200
    assert (await client.get("/api/products?q=+", headers=_auth(token))).status_code == 200

    history = await client.get("/api/search/history", headers=_auth(token))

    assert history.json() == []


async def test_catalog_search_matches_tokens_in_any_order(db_session):
    product = Product(
        canonical_key="apple-iphone-13|display|original|-",
        canonical_name="Дисплей Apple iPhone 13 (Оригинал)",
    )
    db_session.add(product)
    await db_session.flush()

    for query in ("дисплей iPhone 13", "iphone 13 дисплей", "ДИСПЛЕЙ APPLE"):
        results, total = await ComparisonService.search_catalog(db_session, query=query)
        assert total == 1, query
        assert results[0]["canonical_name"] == "Дисплей Apple iPhone 13 (Оригинал)"

    _, missing = await ComparisonService.search_catalog(db_session, query="дисплей iphone 14")
    assert missing == 0


async def test_history_is_recorded_once_not_per_page(client, db_session):
    user = await _make_user(db_session, "paging@example.com")
    await _activate_subscription(db_session, user)
    token = create_access_token(user.id)

    for page in (1, 2, 3):
        resp = await client.get(f"/api/products?q=iphone&page={page}", headers=_auth(token))
        assert resp.status_code == 200

    history = (await client.get("/api/search/history", headers=_auth(token))).json()

    assert len(history) == 1


async def test_create_subscription_leaves_single_active_row(db_session):
    user = await _make_user(db_session, "multi@example.com")

    now = datetime.now(timezone.utc)
    for _ in range(2):
        db_session.add(
            Subscription(
                user_id=user.id,
                plan=PlanEnum.basic,
                start_date=now,
                end_date=now + timedelta(days=30),
                is_active=True,
            )
        )
    await db_session.flush()

    created = await PaymentService.create_subscription(db_session, user.id, PlanEnum.advanced)

    active = (
        await db_session.execute(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
        )
    ).scalar()

    assert active == 1
    assert created.plan == PlanEnum.advanced


async def test_deactivated_user_cannot_refresh_tokens(client, db_session):
    user = await _make_user(db_session, "norefresh@example.com")
    refresh_token = create_refresh_token(user.id)

    user.is_active = False
    await db_session.flush()

    resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})

    assert resp.status_code == 401


async def test_deactivated_user_cannot_login(client, db_session):
    user = await _make_user(db_session, "deactivated@example.com")
    user.is_active = False
    await db_session.flush()

    resp = await client.post(
        "/api/auth/login", json={"email": "deactivated@example.com", "password": PASSWORD}
    )

    assert resp.status_code == 401


async def test_active_user_can_still_login(client, db_session):
    await _make_user(db_session, "still-active@example.com")

    resp = await client.post(
        "/api/auth/login", json={"email": "still-active@example.com", "password": PASSWORD}
    )

    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_expired_subscription_is_not_reported_as_current(client, db_session):
    user = await _make_user(db_session, "expired@example.com")
    token = create_access_token(user.id)

    now = datetime.now(timezone.utc)
    db_session.add(
        Subscription(
            user_id=user.id,
            plan=PlanEnum.advanced,
            start_date=now - timedelta(days=40),
            end_date=now - timedelta(days=10),
            is_active=True,
        )
    )
    await db_session.flush()

    resp = await client.get("/api/users/me/subscription", headers=_auth(token))

    assert resp.status_code == 404


async def test_expired_subscription_does_not_block_resubscribing(client, db_session):
    user = await _make_user(db_session, "resub@example.com")
    token = create_access_token(user.id)

    now = datetime.now(timezone.utc)
    db_session.add(
        Subscription(
            user_id=user.id,
            plan=PlanEnum.basic,
            start_date=now - timedelta(days=40),
            end_date=now - timedelta(days=10),
            is_active=True,
        )
    )
    await db_session.flush()

    resp = await client.post(
        "/api/users/me/subscription", json={"plan": "basic"}, headers=_auth(token)
    )

    assert resp.status_code == 201
    assert resp.json()["plan"] == "basic"


async def test_active_subscription_still_blocks_duplicate(client, db_session):
    user = await _make_user(db_session, "active@example.com")
    token = create_access_token(user.id)

    now = datetime.now(timezone.utc)
    db_session.add(
        Subscription(
            user_id=user.id,
            plan=PlanEnum.basic,
            start_date=now,
            end_date=now + timedelta(days=30),
            is_active=True,
        )
    )
    await db_session.flush()

    resp = await client.post(
        "/api/users/me/subscription", json={"plan": "advanced"}, headers=_auth(token)
    )

    assert resp.status_code == 409


async def test_profile_update_returns_valid_response(client, db_session):
    user = await _make_user(db_session, "profile-update@example.com")
    token = create_access_token(user.id)

    resp = await client.patch(
        "/api/users/me",
        json={"full_name": "Новое имя", "company": "ООО Ромашка"},
        headers=_auth(token),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["full_name"] == "Новое имя"
    assert body["company"] == "ООО Ромашка"
    assert body["updated_at"]
