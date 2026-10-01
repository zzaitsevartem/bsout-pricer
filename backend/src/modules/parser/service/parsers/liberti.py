import httpx
from bs4 import BeautifulSoup, Tag

from src.modules.parser.service.base import ParseResult
from src.modules.parser.service.parsers.bitrix_common import (
    MAX_SKU_LEN,
    MAX_TITLE_LEN,
    STATUS_UNKNOWN,
    BitrixParser,
    availability_status,
    category_from_breadcrumbs,
    clean_text,
    extract_labeled_prices,
    listing_category,
    make_soup,
    merge_stock_status,
    microdata_price,
    microdata_value,
    product_scope,
    resolve_stock,
    stock_qty_from_text,
    stock_status_from_text,
    strip_label_prefix,
    tag_value,
    truncate,
)

STORE_SLUG = "liberti"
STORE_NAME = "Либерти"
BASE_URL = "https://liberti.ru"

ITEM_SELECTOR = ".product-list-item"
ITEM_NAME_SELECTOR = ".product-list-item__name-link"
ITEM_IMAGE_SELECTOR = ".product-list-item__image"
ITEM_PROPS_SELECTOR = ".product-list-item__props"
ITEM_ARTICLE_SELECTOR = ".product-list-item__article"
ITEM_AVAILABILITY_SELECTOR = ".product-list-item__availability"
ITEM_PRICE_BLOCK_SELECTOR = ".product-list-item__price"
ITEM_PRICE_VALUE_SELECTOR = ".product-list-item__price-value"
ITEM_PRICE_NAME_SELECTOR = ".product-list-item__price-name"

CARD_PRICE_BLOCK_SELECTOR = ".product__price"
CARD_PRICE_VALUE_SELECTOR = ".product__price-value"
CARD_PRICE_NAME_SELECTOR = ".product__price-name"
CARD_ARTICLE_SELECTOR = ".product__article-value"
CARD_AVAILABILITY_SELECTOR = ".product-offer-availability__list"


class LibertiParser(BitrixParser):
    sitemap_path = "/sitemap_index.xml"
    search_path = "/search/"
    search_param = "q"
    product_url_markers = (".html",)

    def __init__(self, client: httpx.AsyncClient | None = None):
        super().__init__(STORE_SLUG, STORE_NAME, BASE_URL, client=client)

    def parse_listing(self, markup: str | None, page_url: str = "") -> list[ParseResult]:
        soup = make_soup(markup)
        items = soup.select(ITEM_SELECTOR)
        if not items:
            return []
        category = listing_category(soup)
        results = []
        for item in items:
            result = self._item_to_result(item, category)
            if result is not None:
                results.append(result)
        return results

    def _item_to_result(self, item: Tag, category: str | None) -> ParseResult | None:
        link = item.select_one(ITEM_NAME_SELECTOR)
        title = clean_text(link.get_text(" ", strip=True)) if link else ""
        element_id = clean_text(item.get("data-id"))
        if not title:
            self.log_error(f"listing item without title: {element_id or 'unknown'}")
            return None

        prices = extract_labeled_prices(
            item,
            ITEM_PRICE_BLOCK_SELECTOR,
            ITEM_PRICE_VALUE_SELECTOR,
            ITEM_PRICE_NAME_SELECTOR,
        )
        price_retail = prices.get("retail") or prices.get("opt")
        if price_retail is None:
            self.log_error(f"no price for listing item: {title}")
            return None

        article_tag = item.select_one(ITEM_ARTICLE_SELECTOR)
        article = strip_label_prefix(article_tag.get_text(" ", strip=True)) if article_tag else ""
        source_sku = article or element_id
        if not source_sku:
            self.log_error(f"no sku for listing item: {title}")
            return None

        availability_tag = item.select_one(ITEM_AVAILABILITY_SELECTOR)
        availability_text = (
            clean_text(availability_tag.get_text(" ", strip=True)) if availability_tag else ""
        )
        stock_qty = stock_qty_from_text(availability_text)
        stock_status = resolve_stock(stock_status_from_text(availability_text), stock_qty)
        if stock_status == STATUS_UNKNOWN:
            self.log_error(f"no stock info for listing item: {title}")

        props_tag = item.select_one(ITEM_PROPS_SELECTOR)
        image_tag = item.select_one(ITEM_IMAGE_SELECTOR)
        url = self.absolute(link.get("href")) if link else ""

        return ParseResult(
            source_sku=truncate(source_sku, MAX_SKU_LEN),
            title=truncate(title, MAX_TITLE_LEN),
            price_retail=price_retail,
            price_opt=prices.get("opt"),
            price_old=prices.get("old"),
            description=clean_text(props_tag.get_text(" ", strip=True)) if props_tag else None,
            image_url=self.absolute(image_tag.get("src")) if image_tag else None,
            category=category,
            stock_status=stock_status,
            stock_qty=stock_qty,
            url=url,
            raw={
                "element_id": element_id,
                "article": article,
                "availability_text": availability_text,
                "source": "listing",
            },
        )

    def parse_card(self, markup: str | None, url: str = "") -> ParseResult | None:
        soup = make_soup(markup)
        scope = product_scope(soup)
        if scope is soup and soup.select_one(CARD_PRICE_BLOCK_SELECTOR) is None:
            return None

        title = microdata_value(scope, "name")
        if not title:
            heading = soup.select_one("h1")
            title = clean_text(heading.get_text(" ", strip=True)) if heading else ""
        if not title:
            self.log_error(f"no title on card {url}")
            return None

        prices = extract_labeled_prices(
            scope,
            CARD_PRICE_BLOCK_SELECTOR,
            CARD_PRICE_VALUE_SELECTOR,
            CARD_PRICE_NAME_SELECTOR,
        )
        price_retail = prices.get("retail") or prices.get("opt") or microdata_price(scope)
        if price_retail is None:
            self.log_error(f"no price on card {url}")
            return None

        article_tag = scope.select_one(CARD_ARTICLE_SELECTOR)
        source_sku = clean_text(article_tag.get_text(" ", strip=True)) if article_tag else ""
        source_sku = source_sku or microdata_value(scope, "sku")
        if not source_sku:
            self.log_error(f"no sku on card {url}")
            return None

        availability_tag = scope.select_one(CARD_AVAILABILITY_SELECTOR) or soup.select_one(
            CARD_AVAILABILITY_SELECTOR
        )
        availability_text = (
            clean_text(availability_tag.get_text(" ", strip=True)) if availability_tag else ""
        )
        stock_qty = stock_qty_from_text(availability_text)
        stock_status = resolve_stock(
            merge_stock_status(
                availability_status(scope), stock_status_from_text(availability_text)
            ),
            stock_qty,
        )
        if stock_status == STATUS_UNKNOWN:
            self.log_error(f"no stock info on card {url}")

        image = microdata_value(scope, "image")
        canonical = self._canonical_url(soup) or microdata_value(scope, "url")

        return ParseResult(
            source_sku=truncate(source_sku, MAX_SKU_LEN),
            title=truncate(title, MAX_TITLE_LEN),
            price_retail=price_retail,
            price_opt=prices.get("opt"),
            price_old=prices.get("old"),
            description=microdata_value(scope, "description") or None,
            image_url=self.absolute(image) if image else None,
            category=category_from_breadcrumbs(soup, title),
            stock_status=stock_status,
            stock_qty=stock_qty,
            url=url or self.absolute(canonical),
            raw={
                "article": source_sku,
                "availability_text": availability_text,
                "source": "card",
            },
        )

    @staticmethod
    def _canonical_url(soup: BeautifulSoup) -> str:
        return tag_value(soup.select_one('link[rel="canonical"]'))
