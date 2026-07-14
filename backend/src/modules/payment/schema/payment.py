from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.modules.auth.model.user import PlanEnum


class PaymentCreateRequest(BaseModel):
    plan: PlanEnum
    payment_method: str = Field(default="card", max_length=50)


class PaymentResponse(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    plan: PlanEnum
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionUpgradeRequest(BaseModel):
    plan: PlanEnum
