from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class ParseResult:
    external_id: str
    name: str
    price: Decimal
    old_price: Decimal | None = None
    description: str | None = None
    image_url: str | None = None
    category: str | None = None
    in_stock: bool = True
    product_url: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class BaseParser(ABC):
    def __init__(self, store_slug: str, store_name: str, base_url: str):
        self.store_slug = store_slug
        self.store_name = store_name
        self.base_url = base_url
        self.last_run: datetime | None = None
        self.errors: list[str] = []

    @abstractmethod
    async def search(self, query: str) -> list[ParseResult]:
        ...

    @abstractmethod
    async def update_catalog(self) -> list[ParseResult]:
        ...

    async def parse_product(self, url: str) -> ParseResult | None:
        raise NotImplementedError

    def reset_errors(self):
        self.errors = []


class ParserManager:
    def __init__(self):
        self._parsers: dict[str, BaseParser] = {}

    def register(self, parser: BaseParser):
        self._parsers[parser.store_slug] = parser

    def get(self, store_slug: str) -> BaseParser | None:
        return self._parsers.get(store_slug)

    def get_all(self) -> list[BaseParser]:
        return list(self._parsers.values())

    def get_statuses(self) -> list[dict]:
        return [
            {
                "store_slug": p.store_slug,
                "is_running": False,
                "last_run": p.last_run.isoformat() if p.last_run else None,
                "products_found": 0,
                "errors": p.errors,
            }
            for p in self._parsers.values()
        ]


parser_manager = ParserManager()
