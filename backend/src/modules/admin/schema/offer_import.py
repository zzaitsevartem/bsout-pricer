from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from src.modules.products.model.product import STOCK_STATUSES


class OfferImportItem(BaseModel):
    store_slug: str = Field(..., min_length=1, max_length=100)
    source_sku: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    price_retail: Decimal = Field(..., gt=0, max_digits=12, allow_inf_nan=False)
    price_opt: Decimal | None = Field(default=None, gt=0, max_digits=12, allow_inf_nan=False)
    price_old: Decimal | None = Field(default=None, gt=0, max_digits=12, allow_inf_nan=False)
    stock_status: str = Field(default="unknown")
    stock_qty: int | None = Field(default=None, ge=0)
    url: str = Field(default="", max_length=1000)
    image_url: str | None = Field(default=None, max_length=1000)
    description: str | None = None
    category: str | None = Field(default=None, max_length=255)

    model_config = {"extra": "ignore", "str_strip_whitespace": True}

    @field_validator("stock_status", "url", mode="before")
    @classmethod
    def _null_to_default(cls, value: object, info) -> object:
        if value is None:
            return "unknown" if info.field_name == "stock_status" else ""
        return value

    @field_validator("store_slug", "source_sku", "title")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("stock_status")
    @classmethod
    def _known_stock_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in STOCK_STATUSES:
            raise ValueError(f"must be one of: {', '.join(STOCK_STATUSES)}")
        return normalized

    @field_validator("store_slug")
    @classmethod
    def _lower_slug(cls, value: str) -> str:
        return value.strip().lower()


class OfferImportRowError(BaseModel):
    index: int
    reason: str
    store_slug: str | None = None
    source_sku: str | None = None


class OfferImportResponse(BaseModel):
    total: int
    created: int
    updated: int
    skipped: int
    errors: list[OfferImportRowError]
