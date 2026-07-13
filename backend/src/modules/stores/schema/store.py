from datetime import datetime

from pydantic import BaseModel, Field


class StoreResponse(BaseModel):
    id: int
    name: str
    slug: str
    website_url: str
    logo_url: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StoreCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    website_url: str = Field(..., max_length=500)
    logo_url: str | None = Field(None, max_length=500)


class StoreUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    website_url: str | None = Field(None, max_length=500)
    logo_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None
