from datetime import datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, Field

from src.modules.auth.model.user import PlanEnum

TRACKING_LIMIT_REACHED_CODE = "tracking_limit_reached"


class TrackedProductCreateRequest(BaseModel):
    product_id: int = Field(ge=1, validation_alias=AliasChoices("product_id", "productId"))
    target_price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
        validation_alias=AliasChoices("target_price", "targetPrice"),
    )


class TrackedProductUpdateRequest(BaseModel):
    target_price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
        validation_alias=AliasChoices("target_price", "targetPrice"),
    )
    notify_on_any_drop: bool | None = Field(
        default=None, validation_alias=AliasChoices("notify_on_any_drop", "notifyOnAnyDrop")
    )
    is_active: bool | None = Field(
        default=None, validation_alias=AliasChoices("is_active", "isActive")
    )


class TrackedProductResponse(BaseModel):
    id: int
    product_id: int
    canonical_key: str
    canonical_name: str
    target_price: Decimal | None = None
    notify_on_any_drop: bool
    is_active: bool
    initial_price: Decimal | None = None
    last_seen_price: Decimal | None = None
    current_price: Decimal | None = None
    price_delta: Decimal | None = None
    price_delta_pct: float | None = None
    stores_count: int = 0
    target_reached: bool = False
    last_notified_at: datetime | None = None
    created_at: datetime


class TrackedProductListResponse(BaseModel):
    results: list[TrackedProductResponse]
    total: int
    page: int
    per_page: int


class TrackingUsageResponse(BaseModel):
    used: int
    limit: int
    remaining: int
    plan: PlanEnum | None = None
