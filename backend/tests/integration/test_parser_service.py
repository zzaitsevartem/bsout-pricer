from decimal import Decimal

import pytest
from sqlalchemy import func, select

from src.modules.parser.service.base import BaseParser, ParseResult, ParserManager
from src.modules.parser.service.parser_service import DEFAULT_RUN_LIMIT, ParserService
from src.modules.products.model.product import OfferPriceHistory, StoreOffer
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration


class _FakeParser(BaseParser):
    def __init__(self, slug: str, results: list[ParseResult]):
        super().__init__(slug, slug.upper(), "http://example.com")
        self._results = results
        self.received_limits: list[int | None] = []

    async def search(self, query):
        return []

    async def update_catalog(self, limit: int | None = None):
        self.received_limits.append(limit)
        return self._results if limit is None else self._results[:limit]


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
