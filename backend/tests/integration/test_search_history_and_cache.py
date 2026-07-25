import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select

from src.modules.auth.model.user import User
from src.modules.cache import RedisCache
from src.modules.cache.service import redis_cache as redis_cache_module
from src.modules.search.model.search_history import SearchHistory
from src.modules.search.service.search_history_service import SearchHistoryService

pytestmark = pytest.mark.integration


async def _make_user(db, email: str) -> User:
    user = User(email=email, password_hash="x", full_name="Search User", is_active=True)
    db.add(user)
    await db.flush()
    return user


async def _reload(db, entry_id: int) -> SearchHistory:
    db.expunge_all()
    result = await db.execute(select(SearchHistory).where(SearchHistory.id == entry_id))
    return result.scalar_one()


async def _stamp(db, entry: SearchHistory, moment: datetime) -> None:
    entry.created_at = moment
    await db.flush()


@pytest_asyncio.fixture
async def cache_keys():
    redis_cache_module._cache = None
    created: list[str] = []
    namespace = f"test:{uuid.uuid4()}"

    def _make(suffix: str) -> str:
        key = f"{namespace}:{suffix}"
        created.append(key)
        return key

    yield _make

    client = redis_cache_module.get_redis()
    if created:
        await client.delete(*created)
    await client.aclose()
    redis_cache_module._cache = None


async def test_record_persists_entry_for_user(db_session):
    user = await _make_user(db_session, "record@example.com")

    entry = await SearchHistoryService.record(
        db_session,
        user.id,
        "iphone 13 экран",
        filters={"category": "screens", "max_price": 9000},
        results_count=7,
    )
    entry_id = entry.id

    assert entry_id is not None

    stored = await _reload(db_session, entry_id)
    assert stored.user_id == user.id
    assert stored.query == "iphone 13 экран"
    assert stored.filters == {"category": "screens", "max_price": 9000}
    assert stored.results_count == 7
    assert stored.created_at is not None


async def test_record_defaults_to_null_filters_and_zero_results(db_session):
    user = await _make_user(db_session, "defaults@example.com")

    entry = await SearchHistoryService.record(db_session, user.id, "аккумулятор")
    entry_id = entry.id

    stored = await _reload(db_session, entry_id)
    assert stored.filters is None
    assert stored.results_count == 0


async def test_filters_jsonb_dict_round_trips(db_session):
    user = await _make_user(db_session, "jsonb@example.com")
    filters = {
        "category": "batteries",
        "stores": ["mobiplus", "gsmstore"],
        "price": {"min": 500, "max": 12000},
        "in_stock": True,
        "brand": None,
        "rating": 4.5,
    }

    entry = await SearchHistoryService.record(
        db_session, user.id, "battery", filters=filters, results_count=3
    )
    entry_id = entry.id

    stored = await _reload(db_session, entry_id)
    assert isinstance(stored.filters, dict)
    assert stored.filters == filters
    assert stored.filters["price"]["min"] == 500
    assert isinstance(stored.filters["price"]["min"], int)
    assert stored.filters["in_stock"] is True
    assert stored.filters["brand"] is None
    assert stored.filters["stores"] == ["mobiplus", "gsmstore"]


async def test_get_by_user_returns_only_that_users_entries(db_session):
    owner = await _make_user(db_session, "owner@example.com")
    stranger = await _make_user(db_session, "stranger@example.com")

    await SearchHistoryService.record(db_session, owner.id, "mine-one")
    await SearchHistoryService.record(db_session, owner.id, "mine-two")
    await SearchHistoryService.record(db_session, stranger.id, "theirs")

    entries = await SearchHistoryService.get_by_user(db_session, owner.id)

    assert {e.query for e in entries} == {"mine-one", "mine-two"}
    assert all(e.user_id == owner.id for e in entries)


async def test_get_by_user_orders_by_created_at_desc(db_session):
    user = await _make_user(db_session, "ordering@example.com")

    oldest = await SearchHistoryService.record(db_session, user.id, "oldest")
    await _stamp(db_session, oldest, datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc))
    middle = await SearchHistoryService.record(db_session, user.id, "middle")
    await _stamp(db_session, middle, datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc))
    newest = await SearchHistoryService.record(db_session, user.id, "newest")
    await _stamp(db_session, newest, datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc))

    entries = await SearchHistoryService.get_by_user(db_session, user.id)

    assert [e.query for e in entries] == ["newest", "middle", "oldest"]


async def test_get_by_user_respects_limit(db_session):
    user = await _make_user(db_session, "limit@example.com")

    for day in range(1, 6):
        entry = await SearchHistoryService.record(db_session, user.id, f"query-{day}")
        await _stamp(db_session, entry, datetime(2026, 2, day, 12, 0, tzinfo=timezone.utc))

    limited = await SearchHistoryService.get_by_user(db_session, user.id, limit=2)

    assert len(limited) == 2
    assert [e.query for e in limited] == ["query-5", "query-4"]

    everything = await SearchHistoryService.get_by_user(db_session, user.id, limit=50)
    assert len(everything) == 5


async def test_get_by_user_returns_empty_list_for_user_without_history(db_session):
    user = await _make_user(db_session, "empty@example.com")

    assert await SearchHistoryService.get_by_user(db_session, user.id) == []


async def test_cache_set_get_dict_round_trip(cache_keys):
    key = cache_keys("dict")
    value = {"product_id": 42, "price": 1990.5, "store": "mobiplus", "in_stock": True}

    await RedisCache.set(key, value, ttl=60)

    assert await RedisCache.get(key) == value


async def test_cache_set_get_list_round_trip(cache_keys):
    key = cache_keys("list")
    value = [{"id": 1, "price": 100}, {"id": 2, "price": 250}, {"id": 3, "price": 375}]

    await RedisCache.set(key, value, ttl=60)
    restored = await RedisCache.get(key)

    assert isinstance(restored, list)
    assert restored == value


async def test_cache_get_missing_key_returns_none(cache_keys):
    assert await RedisCache.get(cache_keys("never-written")) is None


async def test_cache_exists_true_after_set_and_false_after_delete(cache_keys):
    key = cache_keys("exists")

    assert await RedisCache.exists(key) is False

    await RedisCache.set(key, {"a": 1}, ttl=60)
    assert await RedisCache.exists(key) is True

    await RedisCache.delete(key)
    assert await RedisCache.exists(key) is False


async def test_cache_expire_shortens_ttl_without_losing_value(cache_keys):
    key = cache_keys("expire")
    client = redis_cache_module.get_redis()

    await RedisCache.set(key, {"price": 1000}, ttl=300)
    assert 0 < await client.ttl(key) <= 300

    await RedisCache.expire(key, 5)
    remaining = await client.ttl(key)

    assert 0 < remaining <= 5
    assert await RedisCache.get(key) == {"price": 1000}


async def test_cached_value_disappears_after_ttl_elapses(cache_keys):
    key = cache_keys("ttl")

    await RedisCache.set(key, {"price": 1234}, ttl=1)
    assert await RedisCache.exists(key) is True

    await asyncio.sleep(1.2)

    assert await RedisCache.get(key) is None
    assert await RedisCache.exists(key) is False


async def test_delete_invalidates_stale_price(cache_keys):
    key = cache_keys("price:product:1")
    stale = {"product_id": 1, "price": 4990, "store": "mobiplus"}

    await RedisCache.set(key, stale, ttl=300)
    assert await RedisCache.get(key) == stale

    await RedisCache.delete(key)

    assert await RedisCache.get(key) is None
    assert await RedisCache.exists(key) is False


async def test_reset_after_invalidation_serves_fresh_price(cache_keys):
    key = cache_keys("price:product:2")

    await RedisCache.set(key, {"product_id": 2, "price": 4990}, ttl=300)
    await RedisCache.delete(key)
    await RedisCache.set(key, {"product_id": 2, "price": 5290}, ttl=300)

    assert await RedisCache.get(key) == {"product_id": 2, "price": 5290}


async def test_acquire_lock_is_exclusive_until_released(cache_keys):
    key = cache_keys("lock:parser:mobiplus")

    assert await RedisCache.acquire_lock(key, ttl=60) is True
    assert await RedisCache.acquire_lock(key, ttl=60) is False

    await RedisCache.release_lock(key)

    assert await RedisCache.acquire_lock(key, ttl=60) is True


async def test_non_json_native_values_are_stored_as_strings(cache_keys):
    key = cache_keys("decimal-price")
    moment = datetime(2026, 7, 25, 9, 30, tzinfo=timezone.utc)

    await RedisCache.set(key, {"price": Decimal("4990.50"), "checked_at": moment}, ttl=60)
    restored = await RedisCache.get(key)

    assert restored["price"] == "4990.50"
    assert restored["price"] != 4990.50
    assert restored["checked_at"] == str(moment)
