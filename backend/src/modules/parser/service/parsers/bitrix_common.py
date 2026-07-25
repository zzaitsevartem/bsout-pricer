import asyncio
import html as html_lib
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import quote_plus, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from src.modules.parser.service.base import BaseParser, ParseResult
from src.modules.parser.service.exceptions import ParserError
from src.modules.parser.service.utils import parse_price, safe_request

USER_AGENT = "BScoutBot/0.1"
REQUEST_TIMEOUT = 30.0
CATALOG_DELAY = 1.0
MAX_TITLE_LEN = 500
MAX_SKU_LEN = 255
MAX_URL_LEN = 1000
MAX_SITEMAPS = 60

STATUS_IN_STOCK = "in_stock"
STATUS_LOW = "low"
STATUS_OUT = "out"
STATUS_PREORDER = "preorder"
STATUS_UNKNOWN = "unknown"

STATUS_PRIORITY = (STATUS_IN_STOCK, STATUS_LOW, STATUS_PREORDER, STATUS_OUT, STATUS_UNKNOWN)

AVAILABILITY_MAP = {
    "instock": STATUS_IN_STOCK,
    "onlineonly": STATUS_IN_STOCK,
    "instoreonly": STATUS_IN_STOCK,
    "limitedavailability": STATUS_LOW,
    "outofstock": STATUS_OUT,
    "soldout": STATUS_OUT,
    "discontinued": STATUS_OUT,
    "preorder": STATUS_PREORDER,
    "presale": STATUS_PREORDER,
    "backorder": STATUS_PREORDER,
}

OUT_WORDS = ("нет в наличии", "нет на складе", "отсутству", "распродан", "закончил", "не в наличии")
PREORDER_WORDS = ("под заказ", "предзаказ", "ожидается", "ожидаем")
LOW_WORDS = ("мало", "заканчива", "ограничен", "последн")
IN_STOCK_WORDS = ("в наличии", "в наличие", "есть", "много", "достаточно", "доступен", "склад")

OPT_PRICE_WORDS = ("опт",)
OLD_PRICE_WORDS = ("стар", "без скидки", "до скидки", "обычная")
RETAIL_PRICE_WORDS = ("розн",)

_SPACE_RE = re.compile(r"[\s\u00a0\u1680\u2000-\u200b\u202f\u205f\u3000\ufeff]+")
_QTY_RE = re.compile(r"(\d+)\s*(?:шт|штук)", re.IGNORECASE)
_CURRENCY_RE = re.compile(r"(?:руб[а-яё]*\.?|р\.|₽|rub)", re.IGNORECASE)
_DIGIT_RUN_RE = re.compile(r"\d+")
_LOC_RE = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.IGNORECASE | re.DOTALL)
_SITEMAP_BLOCK_RE = re.compile(r"<sitemap\b.*?</sitemap>", re.IGNORECASE | re.DOTALL)
_CDATA_RE = re.compile(r"^<!\[CDATA\[(.*?)\]\]>$", re.DOTALL)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return _SPACE_RE.sub(" ", value).strip()


def make_soup(markup: str | None) -> BeautifulSoup:
    if not markup:
        return BeautifulSoup("", "html.parser")
    try:
        return BeautifulSoup(markup, "lxml")
    except Exception:
        return BeautifulSoup(markup, "html.parser")


def tag_value(tag: Tag | None) -> str:
    if tag is None:
        return ""
    for attr in ("content", "href", "data-value", "src"):
        value = tag.get(attr)
        if value:
            return clean_text(value)
    return clean_text(tag.get_text(" ", strip=True))


def to_price(value: str | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    text = clean_text(_CURRENCY_RE.sub(" ", str(value))).strip(" .,")
    if not text:
        return None
    try:
        return parse_price(text)
    except ParserError:
        return None


def strip_label_prefix(text: str | None) -> str:
    cleaned = clean_text(text)
    if ":" not in cleaned:
        return cleaned
    head, tail = cleaned.split(":", 1)
    if len(head) <= 30 and tail.strip():
        return tail.strip()
    return cleaned


def product_scope(soup: BeautifulSoup) -> Tag | BeautifulSoup:
    scope = soup.select_one('[itemtype*="schema.org/Product"]')
    return scope if scope is not None else soup


def microdata_values(root: Tag | BeautifulSoup, prop: str) -> list[str]:
    values = []
    for tag in root.select(f'[itemprop="{prop}"]'):
        value = tag_value(tag)
        if value:
            values.append(value)
    return values


def microdata_value(root: Tag | BeautifulSoup, prop: str) -> str:
    for tag in root.select(f'[itemprop="{prop}"]'):
        for attr in ("content", "href", "src"):
            value = tag.get(attr)
            if value:
                return clean_text(value)
        text = clean_text(tag.get_text(" ", strip=True))
        if text:
            return text
    return ""


def microdata_price(root: Tag | BeautifulSoup) -> Decimal | None:
    offers = root.select_one('[itemprop="offers"]')
    for container in (offers, root):
        if container is None:
            continue
        price = to_price(microdata_value(container, "price"))
        if price is not None:
            return price
    return None


def availability_status(root: Tag | BeautifulSoup) -> str:
    for tag in root.select('[itemprop="availability"]'):
        raw = tag.get("href") or tag.get("content") or tag.get_text(" ", strip=True) or ""
        key = clean_text(raw).rsplit("/", 1)[-1].replace(" ", "").lower()
        if key in AVAILABILITY_MAP:
            return AVAILABILITY_MAP[key]
    return STATUS_UNKNOWN


def stock_status_from_text(text: str | None) -> str:
    value = clean_text(text).lower()
    if not value:
        return STATUS_UNKNOWN
    if any(word in value for word in OUT_WORDS):
        return STATUS_OUT
    if any(word in value for word in PREORDER_WORDS):
        return STATUS_PREORDER
    if any(word in value for word in LOW_WORDS):
        return STATUS_LOW
    if any(word in value for word in IN_STOCK_WORDS):
        return STATUS_IN_STOCK
    return STATUS_UNKNOWN


def merge_stock_status(*statuses: str) -> str:
    present = {status for status in statuses if status}
    for candidate in STATUS_PRIORITY:
        if candidate in present:
            return candidate
    return STATUS_UNKNOWN


def stock_qty_from_text(text: str | None) -> int | None:
    match = _QTY_RE.search(clean_text(text).lower())
    if match is None:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def element_id_from(value: str | None) -> str:
    cleaned = clean_text(value)
    if not cleaned:
        return ""
    for chunk in reversed(re.split(r"[^0-9a-zA-Z]+", cleaned)):
        if chunk.isdigit():
            return chunk
    runs = _DIGIT_RUN_RE.findall(cleaned)
    return runs[-1] if runs else ""


def classify_price_label(label: str | None) -> str:
    value = clean_text(label).lower()
    if any(word in value for word in OPT_PRICE_WORDS):
        return "opt"
    if any(word in value for word in OLD_PRICE_WORDS):
        return "old"
    if any(word in value for word in RETAIL_PRICE_WORDS):
        return "retail"
    return "retail"


def extract_labeled_prices(
    container: Tag | BeautifulSoup | None,
    block_selector: str,
    value_selector: str,
    label_selector: str,
) -> dict[str, Decimal]:
    prices: dict[str, Decimal] = {}
    if container is None:
        return prices
    for block in container.select(block_selector):
        price = to_price(tag_value(block.select_one(value_selector)))
        if price is None:
            continue
        label = block.select_one(label_selector)
        key = classify_price_label(label.get_text(" ", strip=True) if label else "")
        prices.setdefault(key, price)
    return prices


def breadcrumb_names(soup: BeautifulSoup) -> list[str]:
    crumbs = soup.select_one('[itemtype*="schema.org/BreadcrumbList"]')
    if crumbs is None:
        return []
    return [name for name in microdata_values(crumbs, "name") if name]


def listing_category(soup: BeautifulSoup) -> str | None:
    names = breadcrumb_names(soup)
    if len(names) < 2:
        return None
    last = names[-1].lower()
    if any(word in last for word in ("поиск", "результат")):
        return None
    return names[-1]


def resolve_stock(status: str, qty: int | None) -> str:
    if status and status != STATUS_UNKNOWN:
        return status
    if qty is None:
        return STATUS_UNKNOWN
    return STATUS_IN_STOCK if qty > 0 else STATUS_OUT


def category_from_breadcrumbs(soup: BeautifulSoup, title: str) -> str | None:
    names = [name for name in breadcrumb_names(soup) if name and name != title]
    return names[-1] if names else None


def _clean_loc(loc: str) -> str:
    text = loc.strip()
    match = _CDATA_RE.match(text)
    if match:
        text = match.group(1).strip()
    return html_lib.unescape(text)


def parse_sitemap(markup: str | None) -> tuple[list[str], list[str]]:
    if not markup:
        return [], []
    child_locs = []
    for block in _SITEMAP_BLOCK_RE.findall(markup):
        child_locs.extend(_clean_loc(loc) for loc in _LOC_RE.findall(block))
    child_set = set(child_locs)
    page_locs = []
    for loc in _LOC_RE.findall(markup):
        cleaned = _clean_loc(loc)
        if cleaned and cleaned not in child_set:
            page_locs.append(cleaned)
    return [loc for loc in child_locs if loc], page_locs


def truncate(value: str, limit: int) -> str:
    return value[:limit] if value else value


class BitrixParser(BaseParser):
    sitemap_path = "/sitemap.xml"
    search_path = "/search/"
    search_param = "q"
    product_url_markers: tuple[str, ...] = ()
    catalog_delay = CATALOG_DELAY

    def __init__(
        self,
        store_slug: str,
        store_name: str,
        base_url: str,
        client: httpx.AsyncClient | None = None,
    ):
        super().__init__(store_slug, store_name, base_url)
        self._client = client

    def log_error(self, message: str) -> None:
        self.errors.append(message)

    @asynccontextmanager
    async def _http(self):
        if self._client is not None:
            yield self._client
            return
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=REQUEST_TIMEOUT,
        ) as client:
            yield client

    async def fetch(self, url: str, client: httpx.AsyncClient | None = None) -> str | None:
        try:
            if client is not None:
                response = await safe_request(client, url, timeout=REQUEST_TIMEOUT)
                return response.text
            async with self._http() as owned:
                response = await safe_request(owned, url, timeout=REQUEST_TIMEOUT)
                return response.text
        except Exception as exc:
            self.log_error(f"fetch failed {url}: {exc}")
            return None

    def absolute(self, href: str | None) -> str:
        value = clean_text(href)
        if not value:
            return ""
        return truncate(urljoin(self.base_url + "/", value), MAX_URL_LEN)

    def is_product_url(self, url: str) -> bool:
        if not url:
            return False
        netloc = urlparse(url).netloc
        if netloc and netloc != urlparse(self.base_url).netloc:
            return False
        if not self.product_url_markers:
            return True
        return any(marker in url for marker in self.product_url_markers)

    def build_search_url(self, query: str) -> str:
        return f"{self.base_url}{self.search_path}?{self.search_param}={quote_plus(query)}"

    def parse_listing(self, markup: str | None, page_url: str = "") -> list[ParseResult]:
        return []

    def parse_card(self, markup: str | None, url: str = "") -> ParseResult | None:
        return None

    def parse_page(self, markup: str | None, url: str = "") -> ParseResult | None:
        card = self.parse_card(markup, url)
        if card is not None:
            return card
        target = urlparse(url).path
        for item in self.parse_listing(markup, url):
            if target and urlparse(item.url).path == target:
                return item
        return None

    async def search(self, query: str) -> list[ParseResult]:
        if not clean_text(query):
            return []
        search_url = self.build_search_url(query)
        markup = await self.fetch(search_url)
        if markup is None:
            return []
        return self.parse_listing(markup, search_url)

    async def parse_product(self, url: str) -> ParseResult | None:
        target = self.absolute(url)
        markup = await self.fetch(target)
        if markup is None:
            return None
        result = self.parse_page(markup, target)
        if result is None:
            self.log_error(f"no product data at {target}")
        return result

    async def collect_sitemap_urls(
        self,
        limit: int | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> list[str]:
        queue = [self.absolute(self.sitemap_path)]
        visited: set[str] = set()
        seen: set[str] = set()
        urls: list[str] = []
        while queue and len(visited) < MAX_SITEMAPS:
            current = queue.pop(0)
            if not current or current in visited:
                continue
            visited.add(current)
            markup = await self.fetch(current, client=client)
            if markup is None:
                continue
            children, locs = parse_sitemap(markup)
            for child in children:
                absolute_child = self.absolute(child)
                if absolute_child and absolute_child not in visited:
                    queue.append(absolute_child)
            for loc in locs:
                absolute_loc = self.absolute(loc)
                if not self.is_product_url(absolute_loc) or absolute_loc in seen:
                    continue
                seen.add(absolute_loc)
                urls.append(absolute_loc)
                if limit is not None and len(urls) >= limit:
                    return urls
        return urls

    async def update_catalog(
        self,
        limit: int | None = None,
        delay: float | None = None,
    ) -> list[ParseResult]:
        pause = self.catalog_delay if delay is None else delay
        results: list[ParseResult] = []
        async with self._http() as client:
            urls = await self.collect_sitemap_urls(limit=limit, client=client)
            for index, url in enumerate(urls):
                if index and pause:
                    await asyncio.sleep(pause)
                markup = await self.fetch(url, client=client)
                if markup is None:
                    continue
                result = self.parse_page(markup, url)
                if result is None:
                    self.log_error(f"no product data at {url}")
                    continue
                results.append(result)
        self.last_run = datetime.now(timezone.utc)
        return results
