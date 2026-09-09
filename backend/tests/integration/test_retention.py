from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from src.modules.auth.model.user import User
from src.modules.auth.service.auth import hash_password
from src.modules.products.model.product import OfferPriceHistory, StoreOffer
from src.modules.search.model.search_history import SearchHistory
from src.modules.stores.model.store import Store
from src.modules.tracking.service.retention import (
    purge_price_history,
    purge_search_history,
    run_retention,
)
from src.worker import WorkerSettings, prune_history

pytestmark = pytest.mark.integration

NOW = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)


async def _store(db, slug: str) -> Store:
    store = Store(
        name=f"Store {slug}",
        slug=slug,
        website_url=f"https://{slug}.example.com",
        is_active=True,
    )
    db.add(store)
    await db.flush()
    return store


async def _offer(db, store: Store, sku: str) -> StoreOffer:
    offer = StoreOffer(
        store_id=store.id,
        source_sku=sku,
        title=f"Offer {sku}",
        normalized_title=f"offer {sku}",
        price_retail=Decimal("1000.00"),
        stock_status="in_stock",
        url=f"https://{store.slug}.example.com/{sku}",
        is_active=True,
    )
    db.add(offer)
    await db.flush()
    return offer


async def _point(db, offer: StoreOffer, recorded_at: datetime, price: str) -> OfferPriceHistory:
    row = OfferPriceHistory(
        offer_id=offer.id,
        price_retail=Decimal(price),
        stock_status="in_stock",
        recorded_at=recorded_at,
    )
    db.add(row)
    await db.flush()
    return row


async def _user(db, email: str) -> User:
    user = User(
        email=email, password_hash=hash_password("s3cret-pass"), full_name="R", is_active=True
    )
    db.add(user)
    await db.flush()
    return user


async def _history_rows(db, offer_id: int) -> list[OfferPriceHistory]:
    result = await db.execute(
        select(OfferPriceHistory)
        .where(OfferPriceHistory.offer_id == offer_id)
        .order_by(OfferPriceHistory.recorded_at)
    )
    return list(result.scalars().all())


async def test_purge_price_history_drops_old_keeps_fresh(db_session):
    store = await _store(db_session, "retention-fresh")
    offer = await _offer(db_session, store, "sku-fresh")

    for hour in range(3):
        await _point(db_session, offer, NOW - timedelta(days=500, hours=hour), "900.00")
    fresh = await _point(db_session, offer, NOW - timedelta(days=2), "1000.00")
    await db_session.commit()

    stats = await purge_price_history(db_session, now=NOW)

    rows = await _history_rows(db_session, offer.id)
    assert stats["purged"] == 3
    assert [row.id for row in rows] == [fresh.id]


async def test_purge_price_history_keeps_anchor_point_for_offer_without_fresh_data(db_session):
    store = await _store(db_session, "retention-anchor")
    offer = await _offer(db_session, store, "sku-anchor")

    for day in (500, 480, 460):
        await _point(db_session, offer, NOW - timedelta(days=day), "800.00")
    await db_session.commit()

    await purge_price_history(db_session, now=NOW)

    rows = await _history_rows(db_session, offer.id)
    assert len(rows) == 1
    assert rows[0].recorded_at.astimezone(timezone.utc) == NOW - timedelta(days=460)


async def test_downsample_keeps_one_point_per_day(db_session):
    store = await _store(db_session, "retention-downsample")
    offer = await _offer(db_session, store, "sku-downsample")

    day_one = NOW - timedelta(days=300)
    day_two = NOW - timedelta(days=299)
    for hour, price in ((0, "990.00"), (6, "970.00"), (12, "980.00")):
        await _point(db_session, offer, day_one.replace(hour=hour), price)
    for hour, price in ((1, "880.00"), (9, "890.00")):
        await _point(db_session, offer, day_two.replace(hour=hour), price)

    recent = await _point(db_session, offer, NOW - timedelta(days=10), "1010.00")
    for hour in (2, 8):
        await _point(db_session, offer, (NOW - timedelta(days=10)).replace(hour=hour), "1020.00")
    await db_session.commit()

    stats = await purge_price_history(db_session, now=NOW)

    rows = await _history_rows(db_session, offer.id)
    days = [row.recorded_at.astimezone(timezone.utc).date() for row in rows]

    assert stats["downsampled"] == 3
    assert stats["purged"] == 0
    assert days.count(day_one.date()) == 1
    assert days.count(day_two.date()) == 1
    assert days.count(recent.recorded_at.astimezone(timezone.utc).date()) == 3

    kept = {row.recorded_at.astimezone(timezone.utc).date(): row.price_retail for row in rows}
    assert kept[day_one.date()] == Decimal("970.00")
    assert kept[day_two.date()] == Decimal("880.00")


async def test_downsample_does_not_touch_raw_window(db_session):
    store = await _store(db_session, "retention-raw")
    offer = await _offer(db_session, store, "sku-raw")

    base = NOW - timedelta(days=5)
    for hour in range(4):
        await _point(db_session, offer, base.replace(hour=hour), "1000.00")
    await db_session.commit()

    stats = await purge_price_history(db_session, now=NOW)

    rows = await _history_rows(db_session, offer.id)
    assert stats["downsampled"] == 0
    assert stats["purged"] == 0
    assert len(rows) == 4


async def test_price_history_batches_never_exceed_batch_size(db_session):
    store = await _store(db_session, "retention-batch")
    offer = await _offer(db_session, store, "sku-batch")

    for index in range(25):
        await _point(db_session, offer, NOW - timedelta(days=500, minutes=index), "700.00")
    await _point(db_session, offer, NOW - timedelta(days=1), "710.00")
    await db_session.commit()

    stats = await purge_price_history(db_session, batch_size=10, now=NOW)

    rows = await _history_rows(db_session, offer.id)
    assert stats["purged"] == 25
    assert stats["largest_batch"] <= 10
    assert stats["purge_batches"] == 3
    assert len(rows) == 1


async def test_max_batches_caps_the_run(db_session):
    store = await _store(db_session, "retention-cap")
    offer = await _offer(db_session, store, "sku-cap")

    for index in range(20):
        await _point(db_session, offer, NOW - timedelta(days=500, minutes=index), "700.00")
    await _point(db_session, offer, NOW - timedelta(days=1), "710.00")
    await db_session.commit()

    stats = await purge_price_history(db_session, batch_size=5, max_batches=2, now=NOW)

    rows = await _history_rows(db_session, offer.id)
    assert stats["purged"] == 10
    assert stats["purge_batches"] == 2
    assert len(rows) == 11


async def test_purge_search_history_drops_old_keeps_fresh(db_session):
    user = await _user(db_session, "retention-search@example.com")

    for day in (200, 150, 91):
        db_session.add(
            SearchHistory(
                user_id=user.id,
                query=f"old-{day}",
                results_count=1,
                created_at=NOW - timedelta(days=day),
            )
        )
    db_session.add(
        SearchHistory(
            user_id=user.id,
            query="fresh",
            results_count=2,
            created_at=NOW - timedelta(days=3),
        )
    )
    await db_session.commit()

    stats = await purge_search_history(db_session, now=NOW)

    result = await db_session.execute(
        select(SearchHistory.query).where(SearchHistory.user_id == user.id)
    )
    remaining = sorted(result.scalars().all())

    assert stats["purged"] == 3
    assert remaining == ["fresh"]


async def test_search_history_batches_never_exceed_batch_size(db_session):
    user = await _user(db_session, "retention-search-batch@example.com")

    for index in range(12):
        db_session.add(
            SearchHistory(
                user_id=user.id,
                query=f"q-{index}",
                results_count=0,
                created_at=NOW - timedelta(days=200, minutes=index),
            )
        )
    await db_session.commit()

    stats = await purge_search_history(db_session, batch_size=5, now=NOW)

    total = (
        await db_session.execute(
            select(func.count()).select_from(SearchHistory).where(SearchHistory.user_id == user.id)
        )
    ).scalar()

    assert stats["purged"] == 12
    assert stats["largest_batch"] <= 5
    assert stats["purge_batches"] == 3
    assert total == 0


async def test_run_retention_reports_both_tables(db_session):
    store = await _store(db_session, "retention-run")
    offer = await _offer(db_session, store, "sku-run")
    user = await _user(db_session, "retention-run@example.com")

    for index in range(2):
        await _point(db_session, offer, NOW - timedelta(days=500, minutes=index), "700.00")
    await _point(db_session, offer, NOW - timedelta(days=1), "710.00")
    db_session.add(
        SearchHistory(
            user_id=user.id,
            query="stale",
            results_count=0,
            created_at=NOW - timedelta(days=400),
        )
    )
    await db_session.commit()

    stats = await run_retention(db_session, now=NOW)

    assert stats["price_history"]["purged"] == 2
    assert stats["search_history"]["purged"] == 1


async def test_prune_history_job_is_registered_and_runs(db_session):
    assert prune_history in WorkerSettings.functions
    assert any(job.name == "cron:prune_history" for job in WorkerSettings.cron_jobs)

    stats = await prune_history(None, db=db_session)

    assert "price_history" in stats
    assert "search_history" in stats
