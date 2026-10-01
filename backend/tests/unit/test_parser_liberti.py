from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from src.modules.parser.service.exceptions import ParserConnectionError
from src.modules.parser.service.parsers import bitrix_common
from src.modules.parser.service.parsers.bitrix_common import clean_text, parse_sitemap, to_price
from src.modules.parser.service.parsers.liberti import LibertiParser

pytestmark = pytest.mark.unit

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "parsers"
ITEM_URL = "https://liberti.ru/korpus-samsung-galaxy-tab-3-8-0-sm-t310-belyy-high-copy.html"

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://liberti.ru/sitemap_iblock_1.xml</loc></sitemap>
</sitemapindex>
"""

SITEMAP_PAGES = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://liberti.ru/korpus-test.html?id=1&amp;set=2</loc></url>
  <url><loc>https://liberti.ru/kontakty/</loc></url>
</urlset>
"""

CARD_HTML = """
<html><body>
<div class="lb-breadcrumbs" itemscope itemtype="http://schema.org/BreadcrumbList">
  <span itemprop="itemListElement" itemscope itemtype="http://schema.org/ListItem">
    <span itemprop="name">Liberty Project</span>
  </span>
  <span itemprop="itemListElement" itemscope itemtype="http://schema.org/ListItem">
    <span itemprop="name">Корпуса для планшетов</span>
  </span>
</div>
<div class="product" itemscope itemtype="http://schema.org/Product">
  <meta itemprop="name" content="Корпус Samsung Galaxy Tab 3 8.0 SM-T310 (белый) HIGH COPY">
  <span class="product__article-value" itemprop="sku">0L-00031903</span>
  <meta itemprop="description" content="Корпус для планшета Samsung Galaxy Tab 3 8.0.">
  <meta itemprop="image" content="https://liberti.ru/upload/resizer/9f/e242279_0.jpg">
  <div class="product__offer-block" itemprop="offers" itemscope itemtype="http://schema.org/Offer">
    <div class="product__prices">
      <div class="product__price product__price--main">
        <div class="product__price-value product__price-number">
          <span itemprop="price">1310</span> ₽
        </div>
        <div class="product__price-name product__price-text">Розничная цена</div>
      </div>
      <div class="product__price product__price--opt">
        <div class="product__price-value product__price-number">950 ₽</div>
        <div class="product__price-name product__price-text">Оптовая цена</div>
      </div>
    </div>
    <link itemprop="availability" href="http://schema.org/InStock">
    <div class="product-offer-availability__list">Интернет-магазин - 3 штуки</div>
  </div>
</div>
</body></html>
"""

LISTING_OPT_HTML = """
<div class="product-list-item" data-id="242279">
  <a class="product-list-item__name-link" href="/korpus-test.html"><span>Корпус тестовый</span></a>
  <div class="product-list-item__article selectable">Артикул: 0L-00031903</div>
  <div class="product-list-item__prices-block">
    <div class="product-list-item__price product-list-item__price--main">
      <div class="product-list-item__price-value">1 310 ₽</div>
      <div class="product-list-item__price-name">Розничная цена</div>
    </div>
    <div class="product-list-item__price product-list-item__price--opt">
      <div class="product-list-item__price-value">950 ₽</div>
      <div class="product-list-item__price-name">Оптовая цена</div>
    </div>
  </div>
  <div class="product-list-item__availability">В наличии 4 шт.</div>
</div>
"""

LISTING_NO_PRICE_HTML = """
<div class="product-list-item" data-id="242280">
  <a class="product-list-item__name-link" href="/bez-ceny.html"><span>Товар без цены</span></a>
  <div class="product-list-item__article">Артикул: 0L-00000001</div>
  <div class="product-list-item__availability">Нет в наличии</div>
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


def test_parse_listing_from_section_fixture():
    parser = LibertiParser()
    results = parser.parse_listing(read_fixture("liberti_product.html"))

    assert len(results) == 37
    assert all(item.price_retail > 0 for item in results)

    first = results[0]
    assert first.title == "Корпус Samsung Galaxy Tab 3 8.0 SM-T310 (белый) HIGH COPY"
    assert first.source_sku == "0L-00031903"
    assert first.price_retail == Decimal("1310")
    assert first.url == ITEM_URL
    assert first.stock_status == "in_stock"
    assert first.stock_qty == 1
    assert first.image_url.startswith("https://liberti.ru/upload/")
    assert first.category.startswith("Корпуса")
    assert first.raw["element_id"] == "242279"


def test_parse_listing_from_home_fixture():
    parser = LibertiParser()
    results = parser.parse_listing(read_fixture("liberti_home.html"))

    assert len(results) == 32
    assert all(item.source_sku for item in results)
    assert all(item.price_retail > 0 for item in results)
    assert all(item.url.startswith("https://liberti.ru/") for item in results)


def test_listing_extracts_opt_price():
    parser = LibertiParser()
    results = parser.parse_listing(LISTING_OPT_HTML)

    assert len(results) == 1
    item = results[0]
    assert item.price_retail == Decimal("1310")
    assert item.price_opt == Decimal("950")
    assert item.stock_status == "in_stock"
    assert item.stock_qty == 4
    assert item.source_sku == "0L-00031903"


def test_listing_item_without_price_is_skipped():
    parser = LibertiParser()
    results = parser.parse_listing(LISTING_NO_PRICE_HTML)

    assert results == []
    assert any("no price" in error for error in parser.errors)


def test_parse_card_extracts_retail_and_opt():
    parser = LibertiParser()
    result = parser.parse_card(CARD_HTML, ITEM_URL)

    assert result is not None
    assert result.title == "Корпус Samsung Galaxy Tab 3 8.0 SM-T310 (белый) HIGH COPY"
    assert result.source_sku == "0L-00031903"
    assert result.price_retail == Decimal("1310")
    assert result.price_opt == Decimal("950")
    assert result.stock_status == "in_stock"
    assert result.stock_qty == 3
    assert result.category == "Корпуса для планшетов"
    assert result.image_url == "https://liberti.ru/upload/resizer/9f/e242279_0.jpg"
    assert parser.errors == []


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1\xa0310 ₽", Decimal("1310")),
        ("1 310 ₽", Decimal("1310")),
        ("710\xa0₽", Decimal("710")),
        ("1\xa0310,50 руб.", Decimal("1310.50")),
    ],
)
def test_price_normalization(raw, expected):
    assert to_price(raw) == expected


@pytest.mark.parametrize("raw", ["", None, "Цена по запросу", "—"])
def test_price_normalization_returns_none(raw):
    assert to_price(raw) is None


def test_clean_text_strips_nbsp():
    assert clean_text("1\xa0310\xa0₽") == "1 310 ₽"
    assert clean_text(None) == ""


@pytest.mark.parametrize("markup", ["", None, "<html><body>", "<div class='product-list-item'>"])
def test_broken_markup_does_not_raise(markup):
    parser = LibertiParser()

    assert parser.parse_listing(markup) == []
    assert parser.parse_card(markup) is None
    assert parser.parse_page(markup, ITEM_URL) is None


def test_parse_sitemap_unescapes_amp():
    children, pages = parse_sitemap(SITEMAP_PAGES)

    assert children == []
    assert "https://liberti.ru/korpus-test.html?id=1&set=2" in pages


async def test_parse_product_falls_back_to_listing_match():
    async with make_client({".html": read_fixture("liberti_product.html")}) as client:
        parser = LibertiParser(client=client)
        result = await parser.parse_product(ITEM_URL)

    assert result is not None
    assert result.source_sku == "0L-00031903"
    assert result.price_retail == Decimal("1310")


async def test_parse_product_uses_card_markup():
    async with make_client({".html": CARD_HTML}) as client:
        parser = LibertiParser(client=client)
        result = await parser.parse_product(ITEM_URL)

    assert result is not None
    assert result.raw["source"] == "card"
    assert result.price_opt == Decimal("950")


async def test_search_hits_search_path():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, text=read_fixture("liberti_product.html"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        parser = LibertiParser(client=client)
        results = await parser.search("корпус")

    assert seen and "/search/?q=" in seen[0]
    assert len(results) == 37


async def test_update_catalog_walks_sitemap_offline():
    routes = {
        "sitemap_iblock_1.xml": SITEMAP_PAGES,
        "sitemap_index.xml": SITEMAP_INDEX,
        "korpus-test.html": CARD_HTML,
    }
    async with make_client(routes) as client:
        parser = LibertiParser(client=client)
        results = await parser.update_catalog(delay=0)

    assert len(results) == 1
    assert results[0].price_retail == Decimal("1310")
    assert results[0].price_opt == Decimal("950")
    assert parser.last_run is not None


async def test_fetch_failure_is_logged(monkeypatch):
    async def failing_request(*args, **kwargs):
        raise ParserConnectionError("boom")

    monkeypatch.setattr(bitrix_common, "safe_request", failing_request)

    async with make_client({}) as client:
        parser = LibertiParser(client=client)

        assert await parser.parse_product(ITEM_URL) is None
        assert await parser.search("корпус") == []
        assert any("fetch failed" in error for error in parser.errors)
