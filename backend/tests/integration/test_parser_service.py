from datetime import datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest
from sqlalchemy import func, select

from src.modules.cache import RedisCache
from src.modules.parser.service.base import BaseParser, ParseResult, ParserManager
from src.modules.parser.service.exceptions import ParserError, ParserParseError
from src.modules.parser.service.parser_service import DEFAULT_RUN_LIMIT, ParserService
from src.modules.products.model.product import OfferPriceHistory, StoreOffer
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration

parser_service_module = import_module("src.modules.parser.service.parser_service")


class _FakeParser(BaseParser):
    def __init__(
        self,
        slug: str,
        results: list[ParseResult],
        run_errors: list[str] | None = None,
    ):
        super().__init__(slug, slug.upper(), "http://example.com")
        self._results = results
        self._run_errors = run_errors or []
        self.received_limits: list[int | None] = []
        self.received_sections: list[str | None] = []

    async def search(self, query):
        return []

    async def update_catalog(self, limit: int | None = None, section: str | None = None):
        self.received_limits.append(limit)
        self.received_sections.append(section)
        self.errors.extend(self._run_errors)
        results = self._results if limit is None else self._results[:limit]
        if section:
            results = [r for r in results if section in r.url]
        return results


async def _make_store(db, slug: str) -> Store:
    store = Store(name="S", slug=slug, website_url="http://example.com", is_active=True)
    db.add(store)
    await db.flush()
    return store


async def _count(db, model) -> int:
    return (await db.execute(select(func.count()).select_from(model))).scalar()


async def test_upsert_creates_then_updates_and_records_price_change(db_session):
    store = await _make_store(db_session, "up-store")
    svc = ParserService(ParserManager())

    await svc.upsert_offer(
        db_session,
        store.id,
        ParseResult(
            source_sku="A", title="Дисплей", price_retail=Decimal("100"), url="http://example.com/a"
        ),
    )
    await svc.upsert_offer(
        db_session,
        store.id,
        ParseResult(
            source_sku="A", title="Дисплей", price_retail=Decimal("120"), url="http://example.com/a"
        ),
    )
    await svc.upsert_offer(
        db_session,
        store.id,
        ParseResult(
            source_sku="A",
            title="Дисплей",
            price_retail=Decimal("120"),
            stock_status="low",
            url="http://example.com/a",
        ),
    )

    assert await _count(db_session, StoreOffer) == 1
    assert await _count(db_session, OfferPriceHistory) == 2

    offer = (
        await db_session.execute(select(StoreOffer).where(StoreOffer.store_id == store.id))
    ).scalar_one()
    assert offer.price_retail == Decimal("120")
    assert offer.stock_status == "low"
    assert offer.normalized_title == "дисплей"


@pytest.mark.parametrize("price", [Decimal("0"), Decimal("-1"), Decimal("NaN")])
async def test_upsert_rejects_nonpositive_or_nonfinite_price(db_session, price):
    store = await _make_store(db_session, f"invalid-price-{str(price).lower()}")
    svc = ParserService(ParserManager())

    with pytest.raises(ParserParseError):
        await svc.upsert_offer(
            db_session,
            store.id,
            ParseResult(
                source_sku="BAD",
                title="Дисплей",
                price_retail=price,
                url="http://example.com/bad",
            ),
        )

    assert await _count(db_session, StoreOffer) == 0


async def test_run_one_upserts_all_and_reports_done(db_session):
    await _make_store(db_session, "run-store")
    svc = ParserService(ParserManager())
    svc.register(
        _FakeParser(
            "run-store",
            [
                ParseResult(
                    source_sku="X1",
                    title="A",
                    price_retail=Decimal("10"),
                    url="http://example.com/1",
                ),
                ParseResult(
                    source_sku="X2",
                    title="B",
                    price_retail=Decimal("20"),
                    url="http://example.com/2",
                ),
            ],
        )
    )

    result = await svc.run_one(db_session, "run-store", full_sync=True)

    assert result["status"] == "done"
    assert result["upserted"] == 2
    assert await _count(db_session, StoreOffer) == 2


async def test_run_one_skips_invalid_result_and_keeps_valid_offers(db_session):
    await _make_store(db_session, "mixed-store")
    svc = ParserService(ParserManager())
    svc.register(
        _FakeParser(
            "mixed-store",
            [
                ParseResult(
                    source_sku="OK",
                    title="A",
                    price_retail=Decimal("10"),
                    url="http://example.com/ok",
                ),
                ParseResult(
                    source_sku="BAD",
                    title="B",
                    price_retail=Decimal("0"),
                    url="http://example.com/bad",
                ),
            ],
        )
    )

    result = await svc.run_one(db_session, "mixed-store", full_sync=True)

    assert result["upserted"] == 1
    assert result["skipped"] == 1
    assert result["deactivated"] == 0
    assert await _count(db_session, StoreOffer) == 1


def _offers(count: int) -> list[ParseResult]:
    return [
        ParseResult(
            source_sku=f"S{i}",
            title=f"T{i}",
            price_retail=Decimal("10"),
            url=f"http://example.com/{i}",
        )
        for i in range(count)
    ]


async def test_run_one_caps_catalog_by_default(db_session):
    await _make_store(db_session, "cap-store")
    svc = ParserService(ParserManager())
    parser = _FakeParser("cap-store", _offers(3))
    svc.register(parser)

    result = await svc.run_one(db_session, "cap-store")

    assert parser.received_limits == [DEFAULT_RUN_LIMIT]
    assert result["limit"] == DEFAULT_RUN_LIMIT


async def test_run_one_full_sync_lifts_the_cap(db_session):
    await _make_store(db_session, "full-store")
    svc = ParserService(ParserManager())
    parser = _FakeParser("full-store", _offers(3))
    svc.register(parser)

    result = await svc.run_one(db_session, "full-store", full_sync=True)

    assert parser.received_limits == [None]
    assert result["limit"] is None
    assert result["upserted"] == 3


async def test_run_one_explicit_limit_reaches_parser_and_bounds_upserts(db_session):
    await _make_store(db_session, "limit-store")
    svc = ParserService(ParserManager())
    parser = _FakeParser("limit-store", _offers(5))
    svc.register(parser)

    result = await svc.run_one(db_session, "limit-store", full_sync=True, limit=2)

    assert parser.received_limits == [2]
    assert result["limit"] == 2
    assert result["upserted"] == 2
    assert await _count(db_session, StoreOffer) == 2


async def test_enqueue_run_queues_job_and_marks_parser_running(monkeypatch):
    svc = ParserService(ParserManager())
    parser = _FakeParser("queue-store", _offers(1))
    svc.register(parser)

    sent: list[tuple] = []

    async def fake_enqueue(slug, full_sync, limit, section=None):
        sent.append((slug, full_sync, limit, section))
        return "job-1"

    monkeypatch.setattr(parser_service_module, "enqueue_parser_run", fake_enqueue)
    await RedisCache.delete(f"parser:lock:{parser.store_slug}")
    await RedisCache.delete(f"parser:status:{parser.store_slug}")

    result = await svc.enqueue_run("queue-store", full_sync=True)

    assert result == {
        "store_slug": "queue-store",
        "status": "queued",
        "job_id": "job-1",
        "limit": None,
        "section": None,
    }
    assert sent == [("queue-store", True, None, None)]

    status = await RedisCache.get(f"parser:status:{parser.store_slug}")
    assert status["is_running"] is True


async def test_enqueue_run_refuses_while_the_lock_is_held(monkeypatch):
    svc = ParserService(ParserManager())
    parser = _FakeParser("busy-store", _offers(1))
    svc.register(parser)

    async def fail_enqueue(slug, full_sync, limit, section=None):
        raise AssertionError("must not enqueue while a run holds the lock")

    monkeypatch.setattr(parser_service_module, "enqueue_parser_run", fail_enqueue)
    await RedisCache.delete(f"parser:lock:{parser.store_slug}")
    assert await RedisCache.acquire_lock(f"parser:lock:{parser.store_slug}", 60)

    try:
        result = await svc.enqueue_run("busy-store", limit=5)
    finally:
        await RedisCache.release_lock(f"parser:lock:{parser.store_slug}")

    assert result["status"] == "already_running"
    assert result["job_id"] is None
    assert result["limit"] == 5


async def test_enqueue_run_rejects_unknown_parser():
    svc = ParserService(ParserManager())
    with pytest.raises(ParserError):
        await svc.enqueue_run("nope")


async def test_queued_status_keeps_the_previous_products_count(monkeypatch):
    svc = ParserService(ParserManager())
    parser = _FakeParser("keep-store", _offers(1))
    svc.register(parser)

    async def fake_enqueue(slug, full_sync, limit, section=None):
        return "job-2"

    monkeypatch.setattr(parser_service_module, "enqueue_parser_run", fake_enqueue)
    await RedisCache.delete(f"parser:lock:{parser.store_slug}")
    await RedisCache.set(
        f"parser:status:{parser.store_slug}",
        {
            "store_slug": "keep-store",
            "is_running": False,
            "last_run": "2026-07-28T03:00:00+00:00",
            "products_found": 4242,
            "errors": [],
        },
        ttl=60,
    )

    await svc.enqueue_run("keep-store")

    status = await RedisCache.get(f"parser:status:{parser.store_slug}")
    assert status["products_found"] == 4242
    assert status["last_run"] == "2026-07-28T03:00:00+00:00"
    assert status["is_running"] is True


async def test_enqueue_run_does_not_queue_a_second_job_before_the_worker_starts(monkeypatch):
    svc = ParserService(ParserManager())
    parser = _FakeParser("dedup-store", _offers(1))
    svc.register(parser)

    jobs: list[tuple] = []

    async def fake_enqueue(slug, full_sync, limit, section=None):
        jobs.append((slug, full_sync, limit))
        return f"job-{len(jobs)}"

    monkeypatch.setattr(parser_service_module, "enqueue_parser_run", fake_enqueue)
    await RedisCache.delete(f"parser:lock:{parser.store_slug}")
    await RedisCache.delete(f"parser:status:{parser.store_slug}")

    first = await svc.enqueue_run("dedup-store", full_sync=True)
    second = await svc.enqueue_run("dedup-store", full_sync=True)

    assert first["status"] == "queued"
    assert second["status"] == "already_running"
    assert second["job_id"] is None
    assert jobs == [("dedup-store", True, None)]


async def test_run_one_passes_section_to_parser_and_narrows_the_crawl(db_session):
    await _make_store(db_session, "section-store")
    svc = ParserService(ParserManager())
    parser = _FakeParser(
        "section-store",
        [
            ParseResult(
                source_sku="D1",
                title="Дисплей",
                price_retail=Decimal("10"),
                url="http://example.com/displey-a50/",
            ),
            ParseResult(
                source_sku="B1",
                title="АКБ",
                price_retail=Decimal("20"),
                url="http://example.com/akkumulyator-a50/",
            ),
        ],
    )
    svc.register(parser)

    result = await svc.run_one(db_session, "section-store", full_sync=True, section="displey")

    assert parser.received_sections == ["displey"]
    assert result["upserted"] == 1
    offer = (
        await db_session.execute(select(StoreOffer).where(StoreOffer.source_sku == "D1"))
    ).scalar_one()
    assert offer.title == "Дисплей"


async def test_complete_full_sync_deactivates_only_unseen_store_offers(db_session):
    store = await _make_store(db_session, "deactivate-store")
    svc = ParserService(ParserManager())
    retained = [
        ParseResult(
            source_sku=f"KEEP-{index}",
            title=f"A{index}",
            price_retail=Decimal("10"),
            url=f"http://example.com/keep-{index}",
        )
        for index in range(4)
    ]
    stale = ParseResult(
        source_sku="STALE",
        title="B",
        price_retail=Decimal("20"),
        url="http://example.com/stale",
    )
    retained_offers = [await svc.upsert_offer(db_session, store.id, result) for result in retained]
    stale_offer = await svc.upsert_offer(db_session, store.id, stale)
    old = datetime.now(timezone.utc) - timedelta(days=1)
    for offer in retained_offers:
        offer.last_seen_at = old
    stale_offer.last_seen_at = old
    await db_session.flush()
    svc.register(_FakeParser("deactivate-store", retained))

    result = await svc.run_one(db_session, "deactivate-store", full_sync=True)

    for offer in retained_offers:
        await db_session.refresh(offer)
    await db_session.refresh(stale_offer)
    assert result["deactivated"] == 1
    assert result["catalog_coverage"] == 0.8
    assert all(offer.is_active for offer in retained_offers)
    assert stale_offer.is_active is False


async def test_full_sync_below_safe_coverage_never_deactivates(db_session):
    store = await _make_store(db_session, "coverage-store")
    svc = ParserService(ParserManager())
    existing = []
    for index in range(5):
        offer = await svc.upsert_offer(
            db_session,
            store.id,
            ParseResult(
                source_sku=f"OLD-{index}",
                title=f"Old {index}",
                price_retail=Decimal("10"),
                url=f"http://example.com/old-{index}",
            ),
        )
        offer.last_seen_at = datetime.now(timezone.utc) - timedelta(days=1)
        existing.append(offer)
    await db_session.flush()
    svc.register(
        _FakeParser(
            store.slug,
            [
                ParseResult(
                    source_sku="OLD-0",
                    title="Old 0",
                    price_retail=Decimal("10"),
                    url="http://example.com/old-0",
                )
            ],
        )
    )

    result = await svc.run_one(db_session, store.slug, full_sync=True)

    for offer in existing:
        await db_session.refresh(offer)
    assert result["catalog_coverage"] == 0.2
    assert result["deactivated"] == 0
    assert all(offer.is_active for offer in existing)


@pytest.mark.parametrize(
    ("full_sync", "limit", "section", "run_errors"),
    [
        (False, None, None, []),
        (True, 1, None, []),
        (True, None, "display", []),
        (True, None, None, ["catalog page failed"]),
    ],
)
async def test_incomplete_or_uncertain_run_never_deactivates(
    db_session, full_sync, limit, section, run_errors
):
    store = await _make_store(db_session, f"safe-store-{len(run_errors)}-{limit}-{section}")
    svc = ParserService(ParserManager())
    stale = await svc.upsert_offer(
        db_session,
        store.id,
        ParseResult(
            source_sku="STALE",
            title="B",
            price_retail=Decimal("20"),
            url="http://example.com/stale",
        ),
    )
    stale.last_seen_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.flush()
    svc.register(_FakeParser(store.slug, [], run_errors=run_errors))

    result = await svc.run_one(
        db_session,
        store.slug,
        full_sync=full_sync,
        limit=limit,
        section=section,
    )

    await db_session.refresh(stale)
    assert result["deactivated"] == 0
    assert stale.is_active is True
