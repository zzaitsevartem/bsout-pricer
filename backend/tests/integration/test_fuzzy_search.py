from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.middleware.subscription_guard import is_fuzzy_enabled
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.parser.service.utils import normalize_name
from src.modules.products.model.product import StoreOffer
from src.modules.products.service.product_service import ProductService
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration


async def _make_offer(db, title: str) -> None:
    store = Store(name="S", slug="fz-store", website_url="http://example.com", is_active=True)
    db.add(store)
    await db.flush()
    db.add(
        StoreOffer(
            store_id=store.id,
            source_sku="F1",
            title=title,
            normalized_title=normalize_name(title),
            price_retail=Decimal("100"),
            url="http://example.com/1",
        )
    )
    await db.flush()


async def test_fuzzy_finds_typo_while_ilike_does_not(db_session):
    await _make_offer(db_session, "Дисплей iPhone 13")

    _, fuzzy_total = await ProductService.search(db_session, query="дислей iphone 13", fuzzy=True)
    _, ilike_total = await ProductService.search(db_session, query="дислей iphone 13", fuzzy=False)

    assert fuzzy_total >= 1
    assert ilike_total == 0


async def test_is_fuzzy_enabled_only_for_advanced(db_session):
    user = User(email="fz@example.com", password_hash="x", full_name="F", is_active=True)
    db_session.add(user)
    await db_session.flush()

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
    assert await is_fuzzy_enabled(db_session, user.id) is False

    subscription.plan = PlanEnum.advanced
    await db_session.flush()
    assert await is_fuzzy_enabled(db_session, user.id) is True


async def test_expired_advanced_subscription_does_not_enable_fuzzy(db_session):
    user = User(email="exp@example.com", password_hash="x", full_name="E", is_active=True)
    db_session.add(user)
    await db_session.flush()

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

    assert await is_fuzzy_enabled(db_session, user.id) is False
