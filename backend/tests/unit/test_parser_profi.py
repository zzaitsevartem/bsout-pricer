from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from src.modules.parser.service.parsers import profi as profi_module
from src.modules.parser.service.parsers.profi import ProfiParser

pytestmark = pytest.mark.unit

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "parsers"
PRODUCT_URL = (
    "https://siriust.ru/oborudovanie/payalnoe-oborudovanie/zapchasti/"
    "payalnik-dlya-payalnoy-stancii-w.e.p.-852d-852d-878a-878d-907a/"
)
SITEMAP_URL = "https://siriust.ru/sitemap.xml"


@pytest.fixture(scope="module")
def product_html() -> str:
    return (FIXTURES / "profi_product.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def listing_html() -> str:
    return (FIXTURES / "profi_home.html").read_text(encoding="utf-8")


@pytest.fixture
def parser() -> ProfiParser:
    return ProfiParser()


@pytest.fixture(autouse=True)
def _no_waiting(monkeypatch):
    monkeypatch.setattr(profi_module, "REQUEST_DELAY", 0)
    monkeypatch.setattr(profi_module, "REQUEST_BACKOFF", 0)
    monkeypatch.setattr(profi_module, "REQUEST_RETRIES", 1)


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
    assert result.source_sku == "М0950260"
    assert result.title == "Паяльник для паяльной станции W.E.P. 852D+/852D++/878A/878D (907А)"
    assert result.price_retail == Decimal("539")
    assert isinstance(result.price_retail, Decimal)
    assert result.category == "Запчасти"
    assert result.url == PRODUCT_URL
    assert result.image_url.endswith(".jpg")
    assert parser.errors == []


def test_parse_product_html_extracts_wholesale_price(parser, product_html):
    result = parser.parse_product_html(product_html, PRODUCT_URL)

    assert result.price_opt == Decimal("431")
    assert result.price_old is None


def test_parse_product_html_extracts_stock_and_raw(parser, product_html):
    result = parser.parse_product_html(product_html, PRODUCT_URL)

    assert result.stock_status == "in_stock"
    assert result.stock_qty is None
    assert result.raw["product_id"] == "30962"
    assert result.raw["currency"] == "RUB"
    assert result.raw["breadcrumbs"] == ["ОБОРУДОВАНИЕ", "ПАЯЛЬНОЕ ОБОРУДОВАНИЕ", "Запчасти"]
    assert result.description.startswith("Паяльник для паяльных станций")


@pytest.mark.parametrize(
    "broken",
    [
        "",
        "   ",
        "<html><body><p>не тот сайт</p></body></html>",
        "<html><body><div itemtype='http://schema.org/Product'",
        "<!doctype html><html><body>Страница не найдена</body></html>",
    ],
)
def test_broken_or_empty_html_returns_none(parser, broken):
    assert parser.parse_product_html(broken, PRODUCT_URL) is None


def test_product_without_price_returns_none_and_records_error(parser):
    html = (
        '<html><body><div itemtype="http://schema.org/Product">'
        '<meta itemprop="sku" content="М1"><meta itemprop="name" content="Паяльник">'
        "</div></body></html>"
    )
    assert parser.parse_product_html(html, PRODUCT_URL) is None
    assert any("no price" in message for message in parser.errors)


def test_out_of_stock_availability_is_detected(parser):
    html = (
        '<html><body><div itemtype="http://schema.org/Product">'
        '<meta itemprop="sku" content="М2"><meta itemprop="name" content="Паяльник">'
        '<div itemprop="offers"><link itemprop="availability" href="http://schema.org/OutOfStock">'
        '<meta itemprop="price" content="100"></div>'
        "</div></body></html>"
    )
    result = parser.parse_product_html(html, PRODUCT_URL)

    assert result.stock_status == "out"


def test_missing_stock_block_is_unknown_not_fatal(parser):
    html = (
        '<html><body><div itemtype="http://schema.org/Product">'
        '<meta itemprop="sku" content="М3"><meta itemprop="name" content="Паяльник">'
        '<meta itemprop="price" content="100">'
        "</div></body></html>"
    )
    result = parser.parse_product_html(html, PRODUCT_URL)

    assert result is not None
    assert result.stock_status == "unknown"
    assert any("no stock block" in message for message in parser.errors)


def test_price_falls_back_to_markup_and_normalizes_nbsp(parser):
    html = (
        '<html><body><div itemtype="http://schema.org/Product">'
        '<meta itemprop="sku" content="М4"><meta itemprop="name" content="Дисплей">'
        "</div>"
        '<div class="prices-container"><div class="ty-product-prices">'
        '<div class="ty-product-block__price-actual"><span class="ty-price">'
        '<span class="ty-price-num">7\xa0190</span> '
        '<span class="ty-price-num"><span class="ty-rub">Р</span></span>'
        '</span><span class="two_prices_title">Розничная цена</span></div>'
        '<div class="ty-product-block__price-second"><span class="ty-price">'
        '<span class="ty-price-num">6\xa0110</span></span>'
        '<span class="two_prices_title">Оптовая цена</span></div>'
        "</div></div></body></html>"
    )
    result = parser.parse_product_html(html, PRODUCT_URL)

    assert result.price_retail == Decimal("7190")
    assert result.price_opt == Decimal("6110")


def test_ambiguous_price_markup_never_glues_digits(parser):
    html = (
        '<html><body><div itemtype="http://schema.org/Product">'
        '<meta itemprop="sku" content="М5"><meta itemprop="name" content="Дисплей">'
        "</div>"
        '<div class="prices-container"><div class="ty-product-prices">'
        '<div class="ty-product-block__price-actual">'
        '<span class="ty-price">539 Р</span><span class="ty-price">431 Р</span>'
        "</div></div></div></body></html>"
    )
    assert parser.parse_product_html(html, PRODUCT_URL) is None
    assert any("no price" in message for message in parser.errors)


def test_parse_listing_html_reads_all_tiles(parser, listing_html):
    tiles = parser.parse_listing_html(listing_html)

    assert len(tiles) == 39
    assert parser.errors == []

    first = tiles[0]
    assert first.source_sku == "М7767981"
    assert first.price_retail == Decimal("7190")
    assert first.price_opt == Decimal("6110")
    assert first.stock_status == "in_stock"
    assert first.title == "Дисплей для iPhone 11 Pro Max+тачскрин Original Change Glass"
    assert first.url.startswith("https://siriust.ru/zapchasti-dlya-apple-i-psp/")
    assert first.raw["product_id"] == "53454"


def test_parse_listing_html_respects_limit(parser, listing_html):
    assert len(parser.parse_listing_html(listing_html, limit=5)) == 5


def test_parse_listing_html_on_garbage_returns_empty(parser):
    assert parser.parse_listing_html("<html><body>пусто</body></html>") == []


def test_sitemap_index_and_urlset(parser):
    index = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://siriust.ru/sitemap-1.xml</loc></sitemap>"
        "</sitemapindex>"
    )
    nested, pages = parser.parse_sitemap_urls(index)
    assert nested == ["https://siriust.ru/sitemap-1.xml"]
    assert pages == []

    urlset = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{PRODUCT_URL}</loc></url>"
        "<url><loc>https://siriust.ru/index.php?dispatch=pages.view&amp;page_id=1</loc></url>"
        "</urlset>"
    )
    _, pages = parser.parse_sitemap_urls(urlset)
    assert parser.filter_product_urls(pages) == [PRODUCT_URL]


def test_filter_product_urls_dedupes_and_skips_service_pages(parser):
    urls = [
        PRODUCT_URL,
        PRODUCT_URL,
        "https://siriust.ru/",
        "https://siriust.ru/blog/novosti/",
        "https://siriust.ru/index.php?dispatch=products.search",
        "https://other.example/product/",
    ]
    assert parser.filter_product_urls(urls) == [PRODUCT_URL]


def test_build_search_url_uses_cs_cart_dispatch(parser):
    url = parser.build_search_url("дисплей iphone")

    assert url.startswith("https://siriust.ru/?")
    assert "dispatch=products.search" in url
    assert "q=" in url
    assert " " not in url


async def test_parse_product_uses_polite_user_agent(product_html):
    seen: list[httpx.Request] = []
    async with _client({PRODUCT_URL: product_html}, seen) as client:
        parser = ProfiParser(client=client)
        result = await parser.parse_product(PRODUCT_URL)

    assert result is not None
    assert result.price_retail == Decimal("539")
    assert seen[0].headers["user-agent"] == "BScoutBot/0.1"


async def test_parse_product_on_fetch_failure_returns_none_and_logs():
    async with _client({}) as client:
        parser = ProfiParser(client=client)
        result = await parser.parse_product(PRODUCT_URL)

    assert result is None
    assert any("fetch failed" in message for message in parser.errors)


async def test_search_parses_listing_in_one_request(listing_html):
    search_url = ProfiParser().build_search_url("дисплей")
    seen: list[httpx.Request] = []
    async with _client({search_url: listing_html}, seen) as client:
        parser = ProfiParser(client=client)
        results = await parser.search("дисплей")

    assert len(results) == 24
    assert results[0].source_sku == "М7767981"
    assert len(seen) == 1


async def test_search_with_blank_query_makes_no_requests():
    seen: list[httpx.Request] = []
    async with _client({}, seen) as client:
        parser = ProfiParser(client=client)
        assert await parser.search("") == []

    assert seen == []


async def test_update_catalog_walks_sitemap(product_html):
    urlset = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{PRODUCT_URL}</loc></url>"
        "<url><loc>https://siriust.ru/index.php?dispatch=pages.view</loc></url>"
        "</urlset>"
    )
    async with _client({SITEMAP_URL: urlset, PRODUCT_URL: product_html}) as client:
        parser = ProfiParser(client=client)
        results = await parser.update_catalog()

    assert len(results) == 1
    assert results[0].source_sku == "М0950260"
    assert results[0].price_retail == Decimal("539")
    assert results[0].price_opt == Decimal("431")
    assert parser.errors == []


async def test_update_catalog_skips_non_product_pages_without_errors(product_html):
    category_page = "<html><body><h1>Категория</h1><div class='ty-grid-list'></div></body></html>"
    urlset = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{PRODUCT_URL}</loc></url>"
        "<url><loc>https://siriust.ru/oborudovanie/</loc></url>"
        "</urlset>"
    )
    routes = {
        SITEMAP_URL: urlset,
        PRODUCT_URL: product_html,
        "https://siriust.ru/oborudovanie/": category_page,
    }
    async with _client(routes) as client:
        parser = ProfiParser(client=client)
        results = await parser.update_catalog(limit=1)

    assert len(results) == 1
    assert parser.errors == []


async def test_update_catalog_without_products_records_error():
    empty = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<url><loc>https://siriust.ru/index.php?dispatch=pages.view</loc></url>"
        "</urlset>"
    )
    async with _client({SITEMAP_URL: empty}) as client:
        parser = ProfiParser(client=client)
        results = await parser.update_catalog()

    assert results == []
    assert any("catalog is empty" in message for message in parser.errors)
