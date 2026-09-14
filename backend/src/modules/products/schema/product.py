from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class StoreRef(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: int
    store_id: int
    category_id: int | None
    product_id: int | None
    source_sku: str
    title: str
    description: str | None
    image_url: str | None
    price_retail: Decimal
    price_opt: Decimal | None
    price_old: Decimal | None
    currency: str
    stock_status: str
    stock_qty: int | None
    url: str
    last_seen_at: datetime
    is_cheapest: bool = False
    store: StoreRef | None = None

    model_config = {"from_attributes": True}


class ProductCreateRequest(BaseModel):
    store_id: int
    category_id: int | None = None
    source_sku: str = Field(..., max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    normalized_title: str | None = Field(None, max_length=500)
    description: str | None = None
    image_url: str | None = Field(None, max_length=1000)
    price_retail: Decimal = Field(..., gt=0)
    price_opt: Decimal | None = None
    price_old: Decimal | None = None
    currency: str = "RUB"
    stock_status: str = "unknown"
    stock_qty: int | None = None
    url: str = Field(..., max_length=1000)


class ProductSearchParams(BaseModel):
    q: str = Field(default="", max_length=500)
    store: str | None = None
    category: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    in_stock: bool | None = None
    sort_by: str = "price_asc"
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class ProductListResponse(BaseModel):
    results: list[ProductResponse]
    total: int
    page: int
    per_page: int


class PriceHistoryResponse(BaseModel):
    id: int
    offer_id: int
    price_retail: Decimal
    price_opt: Decimal | None
    stock_status: str
    recorded_at: datetime

    model_config = {"from_attributes": True}
