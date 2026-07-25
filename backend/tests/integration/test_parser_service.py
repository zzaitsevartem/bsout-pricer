from decimal import Decimal

import pytest
from sqlalchemy import func, select

from src.modules.parser.service.base import BaseParser, ParseResult, ParserManager
from src.modules.parser.service.parser_service import ParserService
from src.modules.products.model.product import OfferPriceHistory, StoreOffer
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration


class _FakeParser(BaseParser):
    def __init__(self, slug: str, results: list[ParseResult]):
        super().__init__(slug, slug.upper(), "http://example.com")
        self._results = results

    async def search(self, query):
        return []

    async def update_catalog(self):
        return self._results


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

    result = await svc.run_one(db_session, "run-store")

    assert result["status"] == "done"
    assert result["upserted"] == 2
    assert await _count(db_session, StoreOffer) == 2
