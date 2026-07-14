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
    external_id: str
    name: str
    description: str | None
    image_url: str | None
    price: Decimal
    old_price: Decimal | None
    currency: str
    in_stock: bool
    product_url: str
    last_updated: datetime
    is_cheapest: bool = False
    store: StoreRef | None = None

    model_config = {"from_attributes": True}


class ProductCreateRequest(BaseModel):
    store_id: int
    category_id: int | None = None
    external_id: str = Field(..., max_length=255)
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=2000)
    image_url: str | None = Field(None, max_length=500)
    price: Decimal = Field(..., gt=0)
    old_price: Decimal | None = None
    currency: str = "RUB"
    in_stock: bool = True
    product_url: str = Field(..., max_length=1000)


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
    product_id: int
    price: Decimal
    recorded_at: datetime

    model_config = {"from_attributes": True}
