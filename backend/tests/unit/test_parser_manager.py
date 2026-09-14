from decimal import Decimal

import pytest

from src.modules.parser.service.base import BaseParser, ParseResult, ParserManager

pytestmark = pytest.mark.unit


class _StubParser(BaseParser):
    async def search(self, query):
        return []

    async def update_catalog(self, limit=None, section=None):
        return []


def test_parse_result_defaults():
    r = ParseResult(source_sku="x1", title="iPhone", price_retail=Decimal("100"))
    assert r.stock_status == "unknown"
    assert r.price_opt is None
    assert r.price_old is None
    assert r.raw == {}
    assert r.url == ""


def test_manager_registers_and_gets_by_slug():
    mgr = ParserManager()
    p = _StubParser("dns", "DNS", "https://dns.example")
    mgr.register(p)
    assert mgr.get("dns") is p
    assert mgr.get("missing") is None
    assert mgr.get_all() == [p]


def test_manager_status_shape():
    mgr = ParserManager()
    mgr.register(_StubParser("dns", "DNS", "https://dns.example"))
    status = mgr.get_statuses()[0]
    assert status["store_slug"] == "dns"
    assert status["is_running"] is False
    assert status["last_run"] is None
    assert status["errors"] == []
