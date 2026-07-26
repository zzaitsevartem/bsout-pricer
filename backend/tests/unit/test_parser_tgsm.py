from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from src.modules.parser.service.parsers import tgsm as tgsm_module
from src.modules.parser.service.parsers.tgsm import TgsmParser

pytestmark = pytest.mark.unit

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "parsers"
PRODUCT_URL = (
    "https://taggsm.ru/index.php?route=product/product&path=900000_900017&product_id=44990"
)
SITEMAP_URL = "https://taggsm.ru/sitemap.xml"


@pytest.fixture(scope="module")
def product_html() -> str:
    return (FIXTURES / "tgsm_product.html").read_text(encoding="utf-8")


@pytest.fixture
def parser() -> TgsmParser:
    return TgsmParser()


@pytest.fixture(autouse=True)
def _no_waiting(monkeypatch):
    monkeypatch.setattr(tgsm_module, "REQUEST_DELAY", 0)
    monkeypatch.setattr(tgsm_module, "REQUEST_BACKOFF", 0)
    monkeypatch.setattr(tgsm_module, "REQUEST_RETRIES", 1)


def _client(routes: dict[str, str], seen: list[httpx.Request] | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        body = routes.get(str(request.url))
        if body is None:
            return httpx.Response(404, text="not found")
        return httpx.Response(200, text=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)


def test_parse_product_html_extracts_core_fields(parser, product_html):
    result = parser.parse_product_html(product_html, PRODUCT_URL)

    assert result is not None
    assert result.source_sku == "44990"
    assert result.title.startswith("Дисплей для Samsung")
    assert "SM-J250F" in result.title
    assert result.price_retail == Decimal("2000")
    assert isinstance(result.price_retail, Decimal)
    assert result.category == "Дисплеи для телефонов"
    assert result.image_url == "https://taggsm.ru/image/cache/data2018/1530277154052-375x266.jpg"
    assert result.url == PRODUCT_URL
    assert parser.errors == []


def test_parse_product_html_reports_stock_and_branches(parser, product_html):
    result = parser.parse_product_html(product_html, PRODUCT_URL)

    assert result.stock_status == "out"
    assert result.stock_qty is None
    assert result.raw["sku_code"] == "zm314774"
    assert result.raw["currency"] == "RUB"
    assert len(result.raw["branches"]) == 33
    assert set(result.raw["stavropol"]) == {"Ставрополь (Лерм.)", "Ставрополь (Туха.)"}
    assert all(v == "нет в наличии" for v in result.raw["stavropol"].values())


def test_parse_product_html_has_no_wholesale_price(parser, product_html):
    result = parser.parse_product_html(product_html, PRODUCT_URL)

    assert result.price_opt is None
    assert result.price_old is None


@pytest.mark.parametrize(
    "broken",
    [
        "",
        "   ",
        "<html><body><p>не тот сайт</p></body></html>",
        "<html><body><div itemtype='https://schema.org/Product'",
        "<!doctype html><html><head><title>404</title></head><body>Товар не найден</body></html>",
    ],
)
def test_broken_or_empty_html_returns_none(parser, broken):
    assert parser.parse_product_html(broken, PRODUCT_URL) is None


def test_product_without_price_returns_none_and_records_error(parser):
    html = (
        '<html><body><div itemtype="https://schema.org/Product">'
        "<h1 itemprop='name'>Дисплей без цены</h1>"
        "</div></body></html>"
    )
    assert parser.parse_product_html(html, PRODUCT_URL) is None
    assert any("no price" in message for message in parser.errors)


def test_product_without_stock_table_is_unknown_not_fatal(parser):
    html = (
        '<html><body><div itemtype="https://schema.org/Product">'
        "<h1 itemprop='name'>Дисплей</h1>"
        '<meta itemprop="price" content="1500">'
        '<span itemprop="sku">zm1</span>'
        "</div></body></html>"
    )
    result = parser.parse_product_html(html, PRODUCT_URL)

    assert result is not None
    assert result.stock_status == "unknown"
    assert result.stock_qty is None
    assert any("no stock table" in message for message in parser.errors)


def test_price_text_fallback_normalizes_nbsp_and_currency(parser):
    html = (
        '<html><body><div itemtype="https://schema.org/Product">'
        "<h1 itemprop='name'>Дисплей</h1>"
        "<div>Цена: 12\xa0345,50 ₽</div>"
        '<span itemprop="sku">zm2</span>'
        "</div></body></html>"
    )
    result = parser.parse_product_html(html, PRODUCT_URL)

    assert result.price_retail == Decimal("12345.50")


def test_stock_in_one_branch_makes_product_in_stock(parser):
    html = (
        '<html><body><div itemtype="https://schema.org/Product">'
        "<h1 itemprop='name'>Дисплей</h1>"
        '<meta itemprop="price" content="900">'
        '<span itemprop="sku">zm3</span>'
        '<table class="filiallist2">'
        "<tr><td>Адлер</td><td>нет в наличии</td></tr>"
        "<tr><td>Ставрополь (Лерм.)</td><td>3 шт</td></tr>"
        "</table></div></body></html>"
    )
    result = parser.parse_product_html(html, PRODUCT_URL)

    assert result.stock_status == "in_stock"
    assert result.stock_qty == 3


def test_sitemap_index_returns_nested_sitemaps(parser):
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://taggsm.ru/sitemap-1.xml</loc></sitemap>"
        "<sitemap><loc>https://taggsm.ru/sitemap-2.xml</loc></sitemap>"
        "</sitemapindex>"
    )
    nested, pages = parser.parse_sitemap_urls(xml)

    assert nested == ["https://taggsm.ru/sitemap-1.xml", "https://taggsm.ru/sitemap-2.xml"]
    assert pages == []


def test_sitemap_unescapes_ampersands(parser):
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://taggsm.ru/index.php?route=product/product"
        "&amp;path=900000_900017&amp;product_id=44990</loc></url>"
        "<url><loc>https://taggsm.ru/index.php?route=product/product"
        "&amp;amp;path=900000&amp;amp;product_id=44991</loc></url>"
        "</urlset>"
    )
    _, pages = parser.parse_sitemap_urls(xml)
    products = parser.filter_product_urls(pages)

    assert len(products) == 2
    for url in products:
        assert "&amp;" not in url
        assert "&product_id=" in url
    assert products[0] == PRODUCT_URL


def test_filter_product_urls_dedupes_and_drops_non_products(parser):
    urls = [
        PRODUCT_URL,
        PRODUCT_URL,
        "https://taggsm.ru/index.php?route=product/category&path=900000",
        "https://taggsm.ru/about.html",
        "https://taggsm.ru/index.php?route=product/product&product_id=1",
    ]
    assert parser.filter_product_urls(urls) == [
        PRODUCT_URL,
        "https://taggsm.ru/index.php?route=product/product&product_id=1",
    ]


def test_build_search_url_uses_searcho_route_and_encodes_query(parser):
    url = parser.build_search_url("дисплей samsung")

    assert url.startswith("https://taggsm.ru/index.php?route=product/searcho&filter_name=")
    assert " " not in url
    assert "%D0%B4" in url


def test_extract_result_urls_dedupes_and_limits(parser):
    html = (
        "<html><body>"
        f'<a href="{PRODUCT_URL}">товар</a>'
        f'<a href="{PRODUCT_URL}">та же карточка</a>'
        '<a href="/index.php?route=product/product&amp;product_id=7">второй</a>'
        '<a href="/index.php?route=product/category&amp;path=1">категория</a>'
        "</body></html>"
    )
    urls = parser.extract_result_urls(html, limit=5)

    assert urls == [PRODUCT_URL, "https://taggsm.ru/index.php?route=product/product&product_id=7"]


async def test_parse_product_uses_polite_user_agent(product_html):
    seen: list[httpx.Request] = []
    async with _client({PRODUCT_URL: product_html}, seen) as client:
        parser = TgsmParser(client=client)
        result = await parser.parse_product(PRODUCT_URL)

    assert result is not None
    assert result.price_retail == Decimal("2000")
    assert seen[0].headers["user-agent"] == "BScoutBot/0.1"


async def test_parse_product_on_fetch_failure_returns_none_and_logs():
    async with _client({}) as client:
        parser = TgsmParser(client=client)
        result = await parser.parse_product(PRODUCT_URL)

    assert result is None
    assert any("fetch failed" in message for message in parser.errors)


async def test_update_catalog_walks_sitemap_index(product_html):
    index = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://taggsm.ru/sitemap-1.xml</loc></sitemap>"
        "</sitemapindex>"
    )
    leaf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<loc>{PRODUCT_URL.replace('&', '&amp;')}</loc>"
        "<url><loc>https://taggsm.ru/index.php?route=product/category&amp;path=1</loc></url>"
        "</urlset>"
    )
    routes = {
        SITEMAP_URL: index,
        "https://taggsm.ru/sitemap-1.xml": leaf,
        PRODUCT_URL: product_html,
    }
    seen: list[httpx.Request] = []
    async with _client(routes, seen) as client:
        parser = TgsmParser(client=client)
        results = await parser.update_catalog()

    assert len(results) == 1
    assert results[0].source_sku == "44990"
    assert results[0].price_retail == Decimal("2000")
    assert parser.errors == []
    assert [str(r.url) for r in seen] == [
        SITEMAP_URL,
        "https://taggsm.ru/sitemap-1.xml",
        PRODUCT_URL,
    ]


async def test_update_catalog_respects_limit(product_html):
    leaf = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{PRODUCT_URL.replace('&', '&amp;')}</loc></url>"
        "<url><loc>https://taggsm.ru/index.php?route=product/product&amp;product_id=2</loc></url>"
        "</urlset>"
    )
    async with _client({SITEMAP_URL: leaf, PRODUCT_URL: product_html}) as client:
        parser = TgsmParser(client=client)
        results = await parser.update_catalog(limit=1)

    assert len(results) == 1


async def test_update_catalog_without_products_records_error():
    empty = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://taggsm.ru/about.html</loc></url>"
        "</urlset>"
    )
    async with _client({SITEMAP_URL: empty}) as client:
        parser = TgsmParser(client=client)
        results = await parser.update_catalog()

    assert results == []
    assert any("catalog is empty" in message for message in parser.errors)


async def test_search_returns_parsed_products(product_html):
    search_url = TgsmParser().build_search_url("дисплей")
    listing = f'<html><body><a href="{PRODUCT_URL}">товар</a></body></html>'
    async with _client({search_url: listing, PRODUCT_URL: product_html}) as client:
        parser = TgsmParser(client=client)
        results = await parser.search("дисплей")

    assert len(results) == 1
    assert results[0].source_sku == "44990"


async def test_search_with_blank_query_makes_no_requests():
    seen: list[httpx.Request] = []
    async with _client({}, seen) as client:
        parser = TgsmParser(client=client)
        assert await parser.search("   ") == []

    assert seen == []
