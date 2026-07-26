import asyncio
import html as html_lib
import re
from contextlib import asynccontextmanager
from decimal import Decimal
from urllib.parse import quote, urljoin

import httpx
from bs4 import BeautifulSoup

from src.modules.parser.service.base import BaseParser, ParseResult
from src.modules.parser.service.exceptions import ParserError
from src.modules.parser.service.utils import parse_price, safe_request

STORE_SLUG = "profi"
STORE_NAME = "Профи"
DEFAULT_BASE_URL = "https://siriust.ru"
USER_AGENT = "BScoutBot/0.1"
SITEMAP_PATH = "/sitemap.xml"
SEARCH_QUERY = (
    "/?subcats=Y&pcode_from_q=Y&pshort=Y&pfull=Y&pname=Y&pkeywords=Y"
    "&search_performed=Y&dispatch=products.search&q="
)

REQUEST_TIMEOUT = 25.0
REQUEST_RETRIES = 3
REQUEST_BACKOFF = 1.0
CATALOG_CONCURRENCY = 4
REQUEST_DELAY = 0.5
MAX_SEARCH_RESULTS = 24
MAX_SITEMAP_DEPTH = 3

SKIP_URL_PARTS = (
    "/index.php",
    "dispatch=",
    "/blog",
    "/news",
    "/pages/",
    "/promotion",
)

_ID_SUFFIX_RE = re.compile(r"_(\d+)$")
_QTY_RE = re.compile(r"(\d+)\s*шт")
_RETAIL_LABELS = ("розниц", "розничная")
_OPT_LABELS = ("опт",)


def _clean(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def _safe_price(text: str | None) -> Decimal | None:
    if text is None:
        return None
    try:
        return parse_price(text)
    except ParserError:
        return None


def _price_from_block(block) -> Decimal | None:
    if block is None:
        return None
    for node in block.select(".ty-price-num"):
        text = _clean(node.get_text(" ", strip=True))
        if any(ch.isdigit() for ch in text):
            price = _safe_price(text)
            if price is not None:
                return price
    prices = block.select(".ty-price")
    if len(prices) != 1:
        return None
    return _safe_price(_clean(prices[0].get_text(" ", strip=True)))


def _stock_from_text(text: str) -> tuple[str, int | None]:
    lowered = _clean(text).lower()
    if not lowered:
        return "unknown", None
    qty_match = _QTY_RE.search(lowered)
    qty = int(qty_match.group(1)) if qty_match else None
    if "нет" in lowered or "под заказ" in lowered:
        return "out", None
    if "налич" in lowered or "есть" in lowered or (qty is not None and qty > 0):
        return "in_stock", qty
    return "unknown", qty


class ProfiParser(BaseParser):
    def __init__(
        self,
        store_slug: str = STORE_SLUG,
        store_name: str = STORE_NAME,
        base_url: str = DEFAULT_BASE_URL,
        client: httpx.AsyncClient | None = None,
    ):
        super().__init__(store_slug, store_name, base_url)
        self._client = client

    @asynccontextmanager
    async def _session(self):
        if self._client is not None:
            yield self._client
            return
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            yield client

    async def _fetch(self, client: httpx.AsyncClient, url: str) -> str | None:
        try:
            response = await safe_request(
                client,
                url,
                retries=REQUEST_RETRIES,
                backoff=REQUEST_BACKOFF,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
        except ParserError as exc:
            self.errors.append(f"fetch failed: {url} ({exc})")
            return None
        return response.text

    def _absolute(self, url: str | None) -> str:
        if not url:
            return ""
        return urljoin(self.base_url + "/", html_lib.unescape(url.strip()))

    def parse_sitemap_urls(self, xml: str) -> tuple[list[str], list[str]]:
        soup = BeautifulSoup(xml, "xml")
        nested = [
            self._absolute(loc.get_text(strip=True))
            for sitemap in soup.find_all("sitemap")
            for loc in sitemap.find_all("loc")
        ]
        nested_set = set(nested)
        pages = [
            self._absolute(loc.get_text(strip=True))
            for loc in soup.find_all("loc")
            if self._absolute(loc.get_text(strip=True)) not in nested_set
        ]
        return nested, pages

    def filter_product_urls(self, urls: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        root = self.base_url.rstrip("/") + "/"
        for url in urls:
            if not url.startswith(root) or url == root:
                continue
            if any(part in url for part in SKIP_URL_PARTS):
                continue
            if url in seen:
                continue
            seen.add(url)
            result.append(url)
        return result

    async def collect_product_urls(self, client: httpx.AsyncClient) -> list[str]:
        pending = [(self._absolute(SITEMAP_PATH), 0)]
        collected: list[str] = []
        visited: set[str] = set()
        while pending:
            url, depth = pending.pop(0)
            if url in visited or depth > MAX_SITEMAP_DEPTH:
                continue
            visited.add(url)
            xml = await self._fetch(client, url)
            if xml is None:
                continue
            try:
                nested, pages = self.parse_sitemap_urls(xml)
            except Exception as exc:
                self.errors.append(f"sitemap parse failed: {url} ({exc})")
                continue
            collected.extend(pages)
            pending.extend((child, depth + 1) for child in nested)
        return self.filter_product_urls(collected)

    def parse_product_html(self, html: str, url: str = "") -> ParseResult | None:
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as exc:
            self.errors.append(f"html parse failed: {url} ({exc})")
            return None

        block = soup.select_one('[itemtype*="schema.org/Product"]')
        if block is None:
            return None

        title = self._extract_title(soup, block)
        if not title:
            self.errors.append(f"no title: {url}")
            return None

        price_retail = self._extract_retail_price(soup, block)
        if price_retail is None:
            self.errors.append(f"no price: {url}")
            return None

        product_id = self._extract_product_id(soup)
        source_sku = self._extract_sku(soup, block) or product_id
        if not source_sku:
            self.errors.append(f"no sku: {url}")
            return None

        stock_status, stock_qty = self._extract_stock(soup, product_id, url)
        breadcrumbs = self._extract_breadcrumbs(soup)
        canonical = self._extract_canonical(soup) or url

        raw = {"currency": "RUB", "breadcrumbs": breadcrumbs}
        if product_id:
            raw["product_id"] = product_id

        return ParseResult(
            source_sku=source_sku,
            title=title,
            price_retail=price_retail,
            price_opt=_price_from_block(soup.select_one(".ty-product-block__price-second")),
            price_old=self._extract_old_price(soup, price_retail),
            description=self._extract_description(soup, block) or None,
            image_url=self._extract_image(soup, block) or None,
            category=breadcrumbs[-1] if breadcrumbs else None,
            stock_status=stock_status,
            stock_qty=stock_qty,
            url=canonical,
            raw=raw,
        )

    def _extract_title(self, soup: BeautifulSoup, block) -> str:
        node = soup.select_one("h1.ty-product-block-title") or soup.select_one("h1")
        if node is not None:
            text = _clean(node.get_text(" ", strip=True))
            if text:
                return text
        meta = block.select_one("meta[itemprop=name]")
        return _clean(meta.get("content")) if meta is not None else ""

    def _extract_retail_price(self, soup: BeautifulSoup, block) -> Decimal | None:
        meta = block.select_one("meta[itemprop=price]")
        if meta is not None:
            price = _safe_price(meta.get("content"))
            if price is not None:
                return price
        return _price_from_block(soup.select_one(".ty-product-block__price-actual"))

    def _extract_sku(self, soup: BeautifulSoup, block) -> str:
        meta = block.select_one("meta[itemprop=sku]")
        if meta is not None and _clean(meta.get("content")):
            return _clean(meta.get("content"))
        node = soup.select_one(".ty-product-block__sku .ty-control-group__item")
        return _clean(node.get_text(" ", strip=True)) if node is not None else ""

    def _extract_product_id(self, soup: BeautifulSoup) -> str:
        node = soup.select_one(".ty-product-block__sku [id^=sku_update_]")
        if node is None:
            node = soup.select_one("[id^=product_amount_update_]")
        if node is not None:
            match = _ID_SUFFIX_RE.search(node.get("id") or "")
            if match is not None:
                return match.group(1)
        field = soup.select_one('input[name*="[product_id]"]')
        return _clean(field.get("value")) if field is not None else ""

    def _extract_canonical(self, soup: BeautifulSoup) -> str:
        link = soup.select_one("link[rel=canonical]")
        if link is not None and link.get("href"):
            return html_lib.unescape(link.get("href").strip())
        meta = soup.select_one('meta[property="og:url"]')
        if meta is not None and meta.get("content"):
            return html_lib.unescape(meta.get("content").strip())
        return ""

    def _extract_image(self, soup: BeautifulSoup, block) -> str:
        meta = block.select_one("meta[itemprop=image]")
        if meta is not None and meta.get("content"):
            return self._absolute(meta.get("content"))
        og = soup.select_one('meta[property="og:image"]')
        if og is not None and og.get("content"):
            return self._absolute(og.get("content"))
        return ""

    def _extract_description(self, soup: BeautifulSoup, block) -> str:
        meta = block.select_one("meta[itemprop=description]")
        if meta is not None and _clean(meta.get("content")):
            return _clean(html_lib.unescape(meta.get("content")))
        og = soup.select_one('meta[property="og:description"]')
        return _clean(og.get("content")) if og is not None else ""

    def _extract_breadcrumbs(self, soup: BeautifulSoup) -> list[str]:
        crumbs: list[str] = []
        for node in soup.select("[itemprop=itemListElement] [itemprop=name]"):
            text = _clean(node.get("content") or node.get_text(" ", strip=True))
            if text and text.lower() != "главная":
                crumbs.append(text)
        return crumbs

    def _extract_old_price(self, soup: BeautifulSoup, retail: Decimal) -> Decimal | None:
        container = soup.select_one(".prices-container") or soup.select_one(".ty-product-prices")
        if container is None:
            return None
        for selector in ("[id^=old_price_update_]", ".ty-list-price", ".ty-price-old"):
            price = _price_from_block(container.select_one(selector))
            if price is not None and price != retail:
                return price
        return None

    def _extract_stock(
        self, soup: BeautifulSoup, product_id: str, url: str
    ) -> tuple[str, int | None]:
        link = soup.select_one('[itemtype*="schema.org/Product"] link[itemprop=availability]')
        href = (link.get("href") or "").lower() if link is not None else ""
        if "outofstock" in href:
            return "out", None
        if "instock" in href:
            scoped = soup.select_one(f"#product_amount_update_{product_id}") if product_id else None
            qty = _stock_from_text(scoped.get_text(" ", strip=True))[1] if scoped else None
            return "in_stock", qty

        scoped = soup.select_one(f"#product_amount_update_{product_id}") if product_id else None
        if scoped is None:
            scoped = soup.select_one(".ty-qty-in-stock")
        if scoped is None:
            self.errors.append(f"no stock block: {url}")
            return "unknown", None
        return _stock_from_text(scoped.get_text(" ", strip=True))

    def parse_listing_html(self, html: str, limit: int | None = None) -> list[ParseResult]:
        soup = BeautifulSoup(html, "lxml")
        results: list[ParseResult] = []
        for tile in soup.select(".ty-grid-list__item"):
            try:
                item = self._parse_tile(tile)
            except Exception as exc:
                self.errors.append(f"tile parse failed: {exc}")
                continue
            if item is not None:
                results.append(item)
            if limit is not None and len(results) >= limit:
                break
        return results

    def _parse_tile(self, tile) -> ParseResult | None:
        link = tile.select_one("a.product-title") or tile.select_one(".ty-grid-list__item-name a")
        if link is None:
            return None
        title = _clean(link.get("title") or link.get_text(" ", strip=True))
        if not title:
            return None

        price_block = tile.select_one(".ty-grid-list__price")
        price_retail, price_opt = self._tile_prices(price_block)
        if price_retail is None:
            self.errors.append(f"no price in tile: {title}")
            return None

        sku_node = tile.select_one(".ty-sku-item .ty-control-group__item")
        source_sku = _clean(sku_node.get_text(" ", strip=True)) if sku_node is not None else ""
        product_id = ""
        field = tile.select_one('input[name*="[product_id]"]')
        if field is not None:
            product_id = _clean(field.get("value"))
        if not source_sku:
            source_sku = product_id
        if not source_sku:
            return None

        stock_node = tile.select_one(".ty-qty-in-stock")
        stock_status, stock_qty = (
            _stock_from_text(stock_node.get_text(" ", strip=True))
            if stock_node is not None
            else ("unknown", None)
        )

        image = tile.select_one("img.ty-pict, img")
        raw = {"currency": "RUB", "source": "listing"}
        if product_id:
            raw["product_id"] = product_id

        return ParseResult(
            source_sku=source_sku,
            title=title,
            price_retail=price_retail,
            price_opt=price_opt,
            price_old=_price_from_block(tile.select_one("[id^=old_price_update_]")),
            description=None,
            image_url=self._absolute(image.get("src")) if image is not None else None,
            category=None,
            stock_status=stock_status,
            stock_qty=stock_qty,
            url=self._absolute(link.get("href")),
            raw=raw,
        )

    def _tile_prices(self, price_block) -> tuple[Decimal | None, Decimal | None]:
        if price_block is None:
            return None, None
        retail: Decimal | None = None
        opt: Decimal | None = None
        fallback: list[Decimal] = []
        for holder in price_block.select("div"):
            price = _price_from_block(holder)
            if price is None:
                continue
            label_node = holder.select_one(".two_prices_title")
            label = _clean(label_node.get_text(" ", strip=True)).lower() if label_node else ""
            if any(token in label for token in _OPT_LABELS):
                opt = opt or price
            elif any(token in label for token in _RETAIL_LABELS):
                retail = retail or price
            else:
                fallback.append(price)
        if retail is None:
            retail = fallback[0] if fallback else _price_from_block(price_block)
        return retail, opt

    async def _parse_many(self, client: httpx.AsyncClient, urls: list[str]) -> list[ParseResult]:
        semaphore = asyncio.Semaphore(CATALOG_CONCURRENCY)

        async def worker(url: str) -> ParseResult | None:
            async with semaphore:
                html = await self._fetch(client, url)
                await asyncio.sleep(REQUEST_DELAY)
            if html is None:
                return None
            try:
                return self.parse_product_html(html, url)
            except Exception as exc:
                self.errors.append(f"parse failed: {url} ({exc})")
                return None

        parsed = await asyncio.gather(*(worker(url) for url in urls))
        return [item for item in parsed if item is not None]

    async def parse_product(self, url: str) -> ParseResult | None:
        async with self._session() as client:
            html = await self._fetch(client, url)
        if html is None:
            return None
        try:
            return self.parse_product_html(html, url)
        except Exception as exc:
            self.errors.append(f"parse failed: {url} ({exc})")
            return None

    def build_search_url(self, query: str) -> str:
        return self._absolute(SEARCH_QUERY) + quote(query)

    async def search(self, query: str) -> list[ParseResult]:
        if not query or not query.strip():
            return []
        async with self._session() as client:
            html = await self._fetch(client, self.build_search_url(query.strip()))
        if html is None:
            return []
        return self.parse_listing_html(html, limit=MAX_SEARCH_RESULTS)

    async def update_catalog(self, limit: int | None = None) -> list[ParseResult]:
        async with self._session() as client:
            urls = await self.collect_product_urls(client)
            if limit is not None:
                urls = urls[:limit]
            if not urls:
                self.errors.append("catalog is empty: no product urls in sitemap")
                return []
            return await self._parse_many(client, urls)
