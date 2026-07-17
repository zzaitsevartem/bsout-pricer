from datetime import datetime

from pydantic import BaseModel


class UserBriefResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminStatsResponse(BaseModel):
    total_users: int
    active_subscriptions: int
    total_products: int
    total_stores: int
