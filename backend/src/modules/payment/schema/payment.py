from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from src.modules.auth.model.user import PlanEnum


class PaymentCreateRequest(BaseModel):
    plan: PlanEnum
    payment_method: str = Field(default="card", max_length=50)
    idempotence_key: str | None = Field(default=None, max_length=128)


class PaymentResponse(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    currency: str
    plan: PlanEnum
    status: str
    provider: str
    provider_payment_id: str | None = None
    confirmation_url: str | None = None
    description: str | None = None
    subscription_id: int | None = None
    created_at: datetime
    paid_at: datetime | None = None

    model_config = {"from_attributes": True}


class PlanResponse(BaseModel):
    plan: PlanEnum
    name_ru: str
    price: Decimal
    first_payment_price: Decimal
    currency: str = "RUB"
    duration_days: int
    tracked_products: int
    stores: int
    fuzzy_search: bool
    price_alerts: bool
    export_reports: bool
    support_ru: str
    featured: bool
    sort_order: int


class SubscriptionUpgradeRequest(BaseModel):
    plan: PlanEnum


class SubscriptionCancelResponse(BaseModel):
    detail: str
    subscription_id: int
    plan: PlanEnum
    is_active: bool
    auto_renew: bool
    end_date: datetime
    access_until: datetime

    model_config = {"from_attributes": True}


class WebhookEvent(BaseModel):
    type: str | None = None
    event: str | None = None
    object: dict[str, Any] | None = None


class WebhookAck(BaseModel):
    detail: str
    payment_id: int | None = None
    status: str | None = None
