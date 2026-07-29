from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PlanResponse(BaseModel):
    id: int
    slug: str
    name: str
    price: Decimal
    period: str
    discount: str | None
    featured: bool
    features: list[str]
    tooltips: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
