from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.modules.auth.model.user import PlanEnum


class UserResponse(BaseModel):
    id: int
    email: str
    username: str | None
    full_name: str
    phone: str | None
    company: str | None
    is_active: bool
    is_admin: bool
    email_verified_at: datetime | None
    pending_email: str | None
    email_change_old_confirmed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)
    company: str | None = Field(None, max_length=255)
    username: str | None = Field(
        None,
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None


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
