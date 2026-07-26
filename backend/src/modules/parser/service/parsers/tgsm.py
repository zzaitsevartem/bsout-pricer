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

STORE_SLUG = "tgsm"
STORE_NAME = "ТГСМ"
DEFAULT_BASE_URL = "https://taggsm.ru"
USER_AGENT = "BScoutBot/0.1"
SITEMAP_PATH = "/sitemap.xml"
SEARCH_ROUTE = "/index.php?route=product/searcho&filter_name="
PRODUCT_MARKER = "product_id="

REQUEST_TIMEOUT = 45.0
REQUEST_RETRIES = 4
REQUEST_BACKOFF = 1.5
CATALOG_CONCURRENCY = 2
REQUEST_DELAY = 1.0
MAX_SEARCH_RESULTS = 10
MAX_SITEMAP_DEPTH = 3

_PRODUCT_ID_RE = re.compile(r"product_id=(\d+)")
_QTY_RE = re.compile(r"(\d+)\s*шт")
_PRICE_TEXT_RE = re.compile(r"Цена\s*:\s*([\d\s .,]+)")


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


def _branch_state(text: str) -> tuple[bool | None, int | None]:
    lowered = _clean(text).lower()
    if not lowered:
        return None, None
    qty_match = _QTY_RE.search(lowered)
    qty = int(qty_match.group(1)) if qty_match else None
    if "нет" in lowered:
        return False, None
    if qty is not None:
        return qty > 0, qty
    if "налич" in lowered or "есть" in lowered or "мало" in lowered:
        return True, None
    return None, None


class TgsmParser(BaseParser):
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
        for url in urls:
            if PRODUCT_MARKER not in url:
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

        if soup.select_one('[itemtype*="schema.org/Product"]') is None:
            return None

        title = self._extract_title(soup)
        if not title:
            self.errors.append(f"no title: {url}")
            return None

        price_retail = self._extract_price(soup)
        if price_retail is None:
            self.errors.append(f"no price: {url}")
            return None

        source_sku, sku_code = self._extract_sku(soup, url)
        if not source_sku:
            self.errors.append(f"no sku: {url}")
            return None

        stock_status, stock_qty, branches = self._extract_stock(soup, url)
        breadcrumbs = self._extract_breadcrumbs(soup)
        canonical = self._extract_canonical(soup) or url

        raw = {"currency": "RUB", "breadcrumbs": breadcrumbs}
        if sku_code:
            raw["sku_code"] = sku_code
        if branches:
            raw["branches"] = branches
            raw["stavropol"] = {k: v for k, v in branches.items() if "ставропол" in k.lower()}

        return ParseResult(
            source_sku=source_sku,
            title=title,
            price_retail=price_retail,
            price_opt=None,
            price_old=self._extract_old_price(soup, price_retail),
            description=self._extract_description(soup) or None,
            image_url=self._extract_image(soup) or None,
            category=breadcrumbs[-1] if breadcrumbs else None,
            stock_status=stock_status,
            stock_qty=stock_qty,
            url=canonical,
            raw=raw,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        node = soup.select_one("h1[itemprop=name]") or soup.select_one("h1")
        if node is not None:
            text = _clean(node.get_text(" ", strip=True))
            if text:
                return text
        meta = soup.select_one("meta[itemprop=name]") or soup.select_one(
            'meta[property="og:title"]'
        )
        return _clean(meta.get("content")) if meta is not None else ""

    def _extract_price(self, soup: BeautifulSoup) -> Decimal | None:
        meta = soup.select_one("meta[itemprop=price], [itemprop=price][content]")
        if meta is not None:
            price = _safe_price(meta.get("content"))
            if price is not None:
                return price
        node = soup.find(string=_PRICE_TEXT_RE)
        if node is not None:
            match = _PRICE_TEXT_RE.search(str(node))
            if match is not None:
                return _safe_price(match.group(1))
        return None

    def _extract_sku(self, soup: BeautifulSoup, url: str) -> tuple[str, str]:
        sku_node = soup.select_one("[itemprop=sku]")
        sku_code = _clean(sku_node.get_text(strip=True)) if sku_node is not None else ""
        if not sku_code:
            product_id_meta = soup.select_one("meta[itemprop=productID]")
            if product_id_meta is not None:
                sku_code = _clean(product_id_meta.get("content")).removeprefix("sku:")

        match = _PRODUCT_ID_RE.search(html_lib.unescape(url or ""))
        if match is None:
            canonical = self._extract_canonical(soup)
            if canonical:
                match = _PRODUCT_ID_RE.search(canonical)
        if match is not None:
            return match.group(1), sku_code
        return sku_code, sku_code

    def _extract_canonical(self, soup: BeautifulSoup) -> str:
        link = soup.select_one("link[rel=canonical]")
        if link is not None and link.get("href"):
            return html_lib.unescape(link.get("href").strip())
        meta = soup.select_one('meta[property="og:url"]')
        if meta is not None and meta.get("content"):
            return html_lib.unescape(meta.get("content").strip())
        return ""

    def _extract_image(self, soup: BeautifulSoup) -> str:
        for selector in ("meta[itemprop=image]", 'meta[property="og:image"]'):
            meta = soup.select_one(selector)
            if meta is not None and meta.get("content"):
                return self._absolute(meta.get("content"))
        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        node = soup.select_one("#tab-description")
        if node is not None:
            text = _clean(node.get_text(" ", strip=True))
            if text:
                return text
        meta = soup.select_one('meta[name=description], meta[property="og:description"]')
        return _clean(meta.get("content")) if meta is not None else ""

    def _extract_breadcrumbs(self, soup: BeautifulSoup) -> list[str]:
        crumbs: list[str] = []
        for node in soup.select("[itemprop=itemListElement] [itemprop=name]"):
            text = _clean(node.get("content") or node.get_text(" ", strip=True))
            if text and text.lower() != "главная":
                crumbs.append(text)
        return crumbs

    def _extract_old_price(self, soup: BeautifulSoup, retail: Decimal) -> Decimal | None:
        anchor = soup.find(string=_PRICE_TEXT_RE)
        container = anchor.parent if anchor is not None else None
        if container is None:
            return None
        for node in container.select("del, s, strike, .price-old"):
            price = _safe_price(node.get_text(" ", strip=True))
            if price is not None and price != retail:
                return price
        return None

    def _extract_stock(
        self, soup: BeautifulSoup, url: str
    ) -> tuple[str, int | None, dict[str, str]]:
        table = soup.select_one("table.filiallist2")
        if table is None:
            self.errors.append(f"no stock table: {url}")
            return "unknown", None, {}

        branches: dict[str, str] = {}
        states: list[bool | None] = []
        quantities: list[int] = []
        for row in table.select("tr"):
            cells = row.select("td")
            if len(cells) < 2:
                continue
            city = _clean(cells[0].get_text(" ", strip=True))
            value = _clean(cells[1].get_text(" ", strip=True))
            if not city:
                continue
            branches[city] = value
            available, qty = _branch_state(value)
            states.append(available)
            if available and qty is not None:
                quantities.append(qty)

        if not states:
            self.errors.append(f"empty stock table: {url}")
            return "unknown", None, branches
        if any(state is True for state in states):
            return "in_stock", (sum(quantities) if quantities else None), branches
        if all(state is False for state in states):
            return "out", None, branches
        return "unknown", None, branches

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
        return self._absolute(SEARCH_ROUTE) + quote(query)

    def extract_result_urls(self, html: str, limit: int = MAX_SEARCH_RESULTS) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        urls = [
            self._absolute(anchor.get("href"))
            for anchor in soup.find_all("a", href=True)
            if PRODUCT_MARKER in html_lib.unescape(anchor.get("href"))
        ]
        return self.filter_product_urls(urls)[:limit]

    async def search(self, query: str) -> list[ParseResult]:
        if not query or not query.strip():
            return []
        async with self._session() as client:
            html = await self._fetch(client, self.build_search_url(query.strip()))
            if html is None:
                return []
            urls = self.extract_result_urls(html)
            if not urls:
                return []
            return await self._parse_many(client, urls)

    async def update_catalog(self, limit: int | None = None) -> list[ParseResult]:
        async with self._session() as client:
            urls = await self.collect_product_urls(client)
            if limit is not None:
                urls = urls[:limit]
            if not urls:
                self.errors.append("catalog is empty: no product urls in sitemap")
                return []
            return await self._parse_many(client, urls)
