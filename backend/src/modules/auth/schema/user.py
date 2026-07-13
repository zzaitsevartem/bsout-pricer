from datetime import datetime

from pydantic import BaseModel, Field

from src.modules.auth.model.user import PlanEnum


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str | None
    company: str | None
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)
    company: str | None = Field(None, max_length=255)


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan: PlanEnum
    start_date: datetime
    end_date: datetime
    is_active: bool
    auto_renew: bool

    model_config = {"from_attributes": True}


class SubscriptionCreateRequest(BaseModel):
    plan: PlanEnum
