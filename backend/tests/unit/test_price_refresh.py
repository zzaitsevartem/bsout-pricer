from decimal import Decimal
from importlib import import_module

import pytest

from src.modules.parser.service.base import ParseResult
from src.modules.parser.service.exceptions import ParserParseError

pytestmark = pytest.mark.unit

price_refresh_module = import_module("src.modules.tracking.service.price_refresh")


class _Db:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


class _Parser:
    def __init__(self, result):
        self._result = result

    async def parse_product(self, url):
        return self._result


class _Manager:
    def __init__(self, parsers):
        self._parsers = parsers

    def get(self, slug):
        return self._parsers.get(slug)


async def test_refresh_reports_missing_parser_and_rejected_result(monkeypatch):
    valid = ParseResult(
        source_sku="OK",
        title="A",
        price_retail=Decimal("10"),
        url="http://example.com/ok",
    )
    rejected = ParseResult(
        source_sku="BAD",
        title="B",
        price_retail=Decimal("0"),
        url="http://example.com/bad",
    )
    rows = [
        (1, valid.url, "valid", 10),
        (2, rejected.url, "rejected", 20),
        (3, "http://example.com/missing", "missing", 30),
    ]

    async def tracked_offer_urls(db, limit):
        return rows

    upserted = []

    async def upsert_offer(db, store_id, result):
        if result.price_retail <= 0:
            raise ParserParseError("invalid price")
        upserted.append((store_id, result.source_sku))

    monkeypatch.setattr(price_refresh_module, "tracked_offer_urls", tracked_offer_urls)
    monkeypatch.setattr(
        price_refresh_module,
        "parser_manager",
        _Manager({"valid": _Parser(valid), "rejected": _Parser(rejected)}),
    )
    monkeypatch.setattr(price_refresh_module.parser_service, "upsert_offer", upsert_offer)
    db = _Db()

    result = await price_refresh_module.refresh_tracked_offers(db, limit=3)

    assert result == {
        "candidates": 3,
        "refreshed": 1,
        "failed": 1,
        "skipped_no_parser": 1,
    }
    assert upserted == [(10, "OK")]
    assert db.commits == 1
