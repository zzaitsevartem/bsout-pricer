from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from src.modules.parser.service.exceptions import ParserConnectionError
from src.modules.parser.service.parsers import bitrix_common
from src.modules.parser.service.parsers.divizion import DivizionParser

pytestmark = pytest.mark.unit

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "parsers"
PRODUCT_URL = (
    "https://divizion126.ru/catalog/aksessuary-dlya-mobilnoy-tekhniki/zashchitnye-styekla/"
    "zashchitnye-styekla-dlya-telefonov/zashchitnoe-steklo-dlya-samsung-/"
    "zashchitnoe-steklo-dlya-samsung-j-seriya/"
    "zashchitnoe-steklo-dlya-samsung-j8-j810-2018-black-hd-ot-10sht-tsena-25r/"
)

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://divizion126.ru/sitemap-iblock-29.xml</loc></sitemap>
  <sitemap><loc>https://divizion126.ru/sitemap-iblock-34.xml</loc></sitemap>
</sitemapindex>
"""

SITEMAP_IBLOCK_29 = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://divizion126.ru/catalog/item-a/?path=1&amp;id=2</loc></url>
  <url><loc>https://divizion126.ru/about/</loc></url>
</urlset>
"""

SITEMAP_IBLOCK_34 = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://divizion126.ru/catalog/item-b/</loc></url>
</urlset>
"""

LISTING_STOCK_HTML = """
<div class="catalog_item" id="bx_1_777">
  <div class="wish_item" data-item="777"></div>
  <div class="item-title"><a href="/catalog/item-777/"><span>Тестовый товар</span></a></div>
  <div class="item-stock"><span class="value">Нет в наличии</span></div>
  <div class="item-stock"><span class="value">Много</span></div>
  <div class="price" data-currency="RUB" data-value="1310">
    <span class="price_value">1 310</span>
  </div>
</div>
"""

LISTING_TEXT_PRICE_HTML = """
<div class="catalog_item" id="bx_1_778">
  <div class="wish_item" data-item="778"></div>
  <div class="item-title"><a href="/catalog/item-778/"><span>Товар без data-value</span></a></div>
  <div class="item-stock"><span class="value">Нет в наличии</span></div>
  <div class="prices"><span class="price_value">1 310 ₽</span></div>
</div>
"""

LISTING_NO_PRICE_HTML = """
<div class="catalog_item" id="bx_1_779">
  <div class="wish_item" data-item="779"></div>
  <div class="item-title"><a href="/catalog/item-779/"><span>Товар без цены</span></a></div>
  <div class="item-stock"><span class="value">Достаточно</span></div>
</div>
"""


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def make_client(routes: dict[str, str]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        target = str(request.url)
        for marker, body in routes.items():
            if marker in target:
                return httpx.Response(
                    200, text=body, headers={"content-type": "text/html; charset=utf-8"}
                )
        return httpx.Response(404, text="not found")

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_parse_card_from_fixture():
    parser = DivizionParser()
    result = parser.parse_card(read_fixture("divizion_product.html"), PRODUCT_URL)

    assert result is not None
    assert result.title.startswith("Защитное стекло для Samsung J8 (J810 2018) Black HD+")
    assert result.price_retail == Decimal("57")
    assert result.source_sku == "37939"
    assert result.stock_status == "in_stock"
    assert result.image_url.startswith("https://divizion126.ru/upload/")
    assert result.category == "Защитное стекло для Samsung J,M серия"
    assert result.description
    assert result.raw["source"] == "card"
    assert parser.errors == []


async def test_parse_product_fetches_and_parses():
    client = make_client({"/catalog/": read_fixture("divizion_product.html")})
    async with client:
        parser = DivizionParser(client=client)
        result = await parser.parse_product(PRODUCT_URL)

    assert result is not None
    assert result.price_retail == Decimal("57")
    assert result.url == PRODUCT_URL
    assert parser.errors == []


def test_parse_listing_from_home_fixture():
    parser = DivizionParser()
    results = parser.parse_listing(read_fixture("divizion_home.html"))

    assert len(results) == 7
    assert all(item.price_retail > 0 for item in results)
    assert all(item.source_sku.isdigit() for item in results)
    assert all(item.url.startswith("https://divizion126.ru/catalog/") for item in results)
    assert all(item.stock_status != "unknown" for item in results)


def test_listing_merges_multi_store_stock():
    parser = DivizionParser()
    results = parser.parse_listing(LISTING_STOCK_HTML)

    assert len(results) == 1
    item = results[0]
    assert item.source_sku == "777"
    assert item.price_retail == Decimal("1310")
    assert item.stock_status == "in_stock"


def test_listing_price_from_text_with_nbsp():
    parser = DivizionParser()
    results = parser.parse_listing(LISTING_TEXT_PRICE_HTML)

    assert len(results) == 1
    assert results[0].price_retail == Decimal("1310")
    assert results[0].stock_status == "out"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("3\xa0990 руб.", Decimal("3990")),
        ("57 руб.", Decimal("57")),
        ("1\xa0310,50 руб.", Decimal("1310.50")),
        ("92", Decimal("92")),
    ],
)
def test_price_normalization_with_rouble_word(raw, expected):
    assert bitrix_common.to_price(raw) == expected


def test_listing_item_without_price_is_skipped():
    parser = DivizionParser()
    results = parser.parse_listing(LISTING_NO_PRICE_HTML)

    assert results == []
    assert any("no price" in error for error in parser.errors)


@pytest.mark.parametrize("markup", ["", None, "<html><body>", "<div class='catalog_item'></div>"])
def test_broken_markup_does_not_raise(markup):
    parser = DivizionParser()

    assert parser.parse_listing(markup) == []
    assert parser.parse_card(markup) is None
    assert parser.parse_page(markup, "https://divizion126.ru/catalog/x/") is None


async def test_search_uses_catalog_query():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, text=read_fixture("divizion_home.html"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        parser = DivizionParser(client=client)
        results = await parser.search("стекло")

    assert seen and "q=" in seen[0] and "/catalog/" in seen[0]
    assert len(results) == 7


async def test_search_with_empty_query_makes_no_request():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request expected")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        parser = DivizionParser(client=client)

        assert await parser.search("  ") == []


async def test_collect_sitemap_urls_unescapes_and_filters():
    routes = {
        "sitemap-iblock-29.xml": SITEMAP_IBLOCK_29,
        "sitemap-iblock-34.xml": SITEMAP_IBLOCK_34,
        "sitemap.xml": SITEMAP_INDEX,
    }
    async with make_client(routes) as client:
        parser = DivizionParser(client=client)
        urls = await parser.collect_sitemap_urls(client=client)

    assert "https://divizion126.ru/catalog/item-a/?path=1&id=2" in urls
    assert "https://divizion126.ru/catalog/item-b/" in urls
    assert all("/about/" not in url for url in urls)


async def test_update_catalog_walks_sitemap_offline():
    routes = {
        "sitemap-iblock-29.xml": SITEMAP_IBLOCK_29,
        "sitemap-iblock-34.xml": SITEMAP_IBLOCK_34,
        "sitemap.xml": SITEMAP_INDEX,
        "/catalog/": read_fixture("divizion_product.html"),
    }
    async with make_client(routes) as client:
        parser = DivizionParser(client=client)
        results = await parser.update_catalog(limit=1, delay=0)

    assert len(results) == 1
    assert results[0].price_retail == Decimal("57")
    assert parser.last_run is not None


async def test_fetch_failure_is_logged(monkeypatch):
    async def failing_request(*args, **kwargs):
        raise ParserConnectionError("boom")

    monkeypatch.setattr(bitrix_common, "safe_request", failing_request)

    async with make_client({}) as client:
        parser = DivizionParser(client=client)
        result = await parser.parse_product(PRODUCT_URL)

    assert result is None
    assert any("fetch failed" in error for error in parser.errors)
