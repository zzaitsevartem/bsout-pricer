from decimal import Decimal

import httpx
import pytest

from src.modules.parser.service.exceptions import ParserConnectionError, ParserParseError
from src.modules.parser.service.parser_service import (
    DEFAULT_RUN_LIMIT,
    FULL_SYNC_LOCK_TTL,
    LOCK_TTL,
    resolve_catalog_limit,
    resolve_lock_ttl,
)
from src.modules.parser.service.utils import (
    compare_products,
    normalize_name,
    parse_price,
    safe_request,
)

pytestmark = pytest.mark.unit


def test_partial_run_is_capped_by_default():
    assert resolve_catalog_limit(full_sync=False, limit=None) == DEFAULT_RUN_LIMIT


def test_full_sync_removes_the_cap():
    assert resolve_catalog_limit(full_sync=True, limit=None) is None


def test_explicit_limit_wins_over_full_sync():
    assert resolve_catalog_limit(full_sync=True, limit=10) == 10
    assert resolve_catalog_limit(full_sync=False, limit=10) == 10


def test_uncapped_run_holds_the_lock_longer_than_a_full_crawl():
    assert resolve_lock_ttl(None) == FULL_SYNC_LOCK_TTL
    assert FULL_SYNC_LOCK_TTL >= 4 * 3600


def test_capped_run_keeps_the_short_lock():
    assert resolve_lock_ttl(DEFAULT_RUN_LIMIT) == LOCK_TTL


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("4 500 ₽", Decimal("4500")),
        ("3 200,50 ₽", Decimal("3200.50")),
        ("1 299", Decimal("1299")),
        ("от 6 800 ₽", Decimal("6800")),
        ("650₽", Decimal("650")),
        ("100.00", Decimal("100.00")),
    ],
)
def test_parse_price_ok(raw, expected):
    assert parse_price(raw) == expected


@pytest.mark.parametrize("raw", ["", "—", "нет в наличии", None, "₽", "-"])
def test_parse_price_bad(raw):
    with pytest.raises(ParserParseError):
        parse_price(raw)


def test_normalize_name():
    assert normalize_name("Дисплей iPhone 13 (оригинал)!") == "дисплей iphone 13 оригинал"
    assert normalize_name("  Аккумулятор   Samsung  ") == "аккумулятор samsung"
    assert normalize_name("") == ""
    assert normalize_name(None) == ""


def test_compare_products():
    assert compare_products("Дисплей iPhone 13", "Дисплей iPhone 13") == 1.0
    assert compare_products("Дисплей iPhone 13 (оригинал)", "дисплей iphone 13 оригинал") == 1.0
    assert compare_products("Дисплей iPhone 13", "Аккумулятор Samsung") < 0.5
    assert compare_products("", "что-то") == 0.0


async def test_safe_request_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectError("boom")
        return httpx.Response(200, text="ok")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        response = await safe_request(client, "http://example.com", retries=3, backoff=0.0)

    assert response.status_code == 200
    assert calls["n"] == 3


async def test_safe_request_gives_up_after_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ParserConnectionError):
            await safe_request(client, "http://example.com", retries=2, backoff=0.0)
