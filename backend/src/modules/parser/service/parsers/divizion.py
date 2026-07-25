from decimal import Decimal

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
    element_id_from,
    listing_category,
    make_soup,
    merge_stock_status,
    microdata_price,
    microdata_value,
    product_scope,
    resolve_stock,
    stock_qty_from_text,
    stock_status_from_text,
    tag_value,
    to_price,
    truncate,
)

STORE_SLUG = "divizion"
STORE_NAME = "Дивизион"
BASE_URL = "https://divizion126.ru"

ITEM_SELECTOR = ".catalog_item"
ITEM_TITLE_SELECTOR = ".item-title a"
ITEM_IMAGE_SELECTOR = ".thumb img"
ITEM_WISH_SELECTOR = ".wish_item"
ITEM_ARTICLE_SELECTOR = ".article_block"
PRICE_SELECTOR = ".price"
PRICE_VALUE_SELECTOR = ".price_value"
OLD_PRICE_SELECTOR = ".price_old, .old_price, .price.discount"
STOCK_SELECTOR = ".item-stock"
CARD_PRICE_SELECTOR = ".price_matrix_block .price, .cost .price"


class DivizionParser(BitrixParser):
    sitemap_path = "/sitemap.xml"
    search_path = "/catalog/"
    search_param = "q"
    product_url_markers = ("/catalog/",)

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

    def _item_to_result(self, item: Tag, category: str | None = None) -> ParseResult | None:
        link = item.select_one(ITEM_TITLE_SELECTOR)
        title = clean_text(link.get_text(" ", strip=True)) if link else ""
        if not title:
            self.log_error("listing item without title")
            return None

        price_retail = self._item_price(item)
        if price_retail is None:
            self.log_error(f"no price for listing item: {title}")
            return None

        source_sku = self._item_sku(item)
        if not source_sku:
            self.log_error(f"no sku for listing item: {title}")
            return None

        stock_texts = [
            clean_text(tag.get_text(" ", strip=True)) for tag in item.select(STOCK_SELECTOR)
        ]
        stock_status = merge_stock_status(*(stock_status_from_text(text) for text in stock_texts))
        if stock_status == STATUS_UNKNOWN:
            self.log_error(f"no stock info for listing item: {title}")

        image_tag = item.select_one(ITEM_IMAGE_SELECTOR)
        article_tag = item.select_one(ITEM_ARTICLE_SELECTOR)
        article = clean_text(article_tag.get_text(" ", strip=True)) if article_tag else ""

        return ParseResult(
            source_sku=truncate(source_sku, MAX_SKU_LEN),
            title=truncate(title, MAX_TITLE_LEN),
            price_retail=price_retail,
            price_opt=None,
            price_old=to_price(tag_value(item.select_one(OLD_PRICE_SELECTOR))),
            description=None,
            image_url=self.absolute(image_tag.get("src")) if image_tag else None,
            category=category,
            stock_status=stock_status,
            stock_qty=None,
            url=self.absolute(link.get("href")) if link else "",
            raw={
                "element_id": source_sku,
                "article": article,
                "stock_texts": stock_texts,
                "source": "listing",
            },
        )

    def _item_price(self, item: Tag) -> Decimal | None:
        price_tag = item.select_one(PRICE_SELECTOR)
        price = to_price(tag_value(price_tag))
        if price is not None:
            return price
        return to_price(tag_value(item.select_one(PRICE_VALUE_SELECTOR)))

    def _item_sku(self, item: Tag) -> str:
        wish = item.select_one(ITEM_WISH_SELECTOR)
        if wish is not None:
            sku = clean_text(wish.get("data-item"))
            if sku:
                return sku
        stock = item.select_one(STOCK_SELECTOR)
        if stock is not None:
            sku = element_id_from(stock.get("data-id"))
            if sku:
                return sku
        return element_id_from(item.get("id"))

    def parse_card(self, markup: str | None, url: str = "") -> ParseResult | None:
        soup = make_soup(markup)
        scope = product_scope(soup)
        if scope is soup:
            return None

        title = microdata_value(scope, "name")
        if not title:
            heading = soup.select_one("h1")
            title = clean_text(heading.get_text(" ", strip=True)) if heading else ""
        if not title:
            self.log_error(f"no title on card {url}")
            return None

        price_retail = microdata_price(scope)
        if price_retail is None:
            price_retail = to_price(tag_value(scope.select_one(CARD_PRICE_SELECTOR)))
        if price_retail is None:
            price_retail = to_price(tag_value(scope.select_one(PRICE_VALUE_SELECTOR)))
        if price_retail is None:
            self.log_error(f"no price on card {url}")
            return None

        source_sku = microdata_value(scope, "sku") or self._item_sku(scope)
        if not source_sku:
            self.log_error(f"no sku on card {url}")
            return None

        stock_tag = scope.select_one(STOCK_SELECTOR)
        stock_text = clean_text(stock_tag.get_text(" ", strip=True)) if stock_tag else ""
        stock_qty = stock_qty_from_text(stock_text)
        stock_status = resolve_stock(
            merge_stock_status(availability_status(scope), stock_status_from_text(stock_text)),
            stock_qty,
        )
        if stock_status == STATUS_UNKNOWN:
            self.log_error(f"no stock info on card {url}")

        image = microdata_value(scope, "image")
        category_path = microdata_value(scope, "category")
        category = self._leaf_category(category_path) or category_from_breadcrumbs(soup, title)

        return ParseResult(
            source_sku=truncate(source_sku, MAX_SKU_LEN),
            title=truncate(title, MAX_TITLE_LEN),
            price_retail=price_retail,
            price_opt=None,
            price_old=to_price(tag_value(scope.select_one(OLD_PRICE_SELECTOR))),
            description=microdata_value(scope, "description") or None,
            image_url=self.absolute(image) if image else None,
            category=category,
            stock_status=stock_status,
            stock_qty=stock_qty,
            url=url or self.absolute(self._canonical_url(soup) or microdata_value(scope, "url")),
            raw={
                "element_id": source_sku,
                "category_path": category_path,
                "stock_text": stock_text,
                "source": "card",
            },
        )

    @staticmethod
    def _leaf_category(path: str | None) -> str | None:
        cleaned = clean_text(path)
        if not cleaned:
            return None
        parts = [part.strip() for part in cleaned.split("/") if part.strip()]
        return parts[-1] if parts else None

    @staticmethod
    def _canonical_url(soup: BeautifulSoup) -> str:
        return tag_value(soup.select_one('link[rel="canonical"]'))
