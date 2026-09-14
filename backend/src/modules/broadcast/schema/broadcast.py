from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.modules.broadcast.model.broadcast import (
    BroadcastAudience,
    BroadcastStatus,
    RecipientStatus,
)


class BroadcastCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    audience: BroadcastAudience
    subject: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=200_000)
    html: str | None = Field(default=None, max_length=500_000)
    recipient_emails: list[EmailStr] | None = None


class BroadcastPreviewRequest(BroadcastCreateRequest):
    pass


class BroadcastPreviewResponse(BaseModel):
    recipient_count: int
    sample_emails: list[str]


class BroadcastResponse(BaseModel):
    id: int
    name: str
    audience: BroadcastAudience
    subject: str
    text: str
    html: str | None
    status: BroadcastStatus
    total_recipients: int
    sent_count: int
    failed_count: int
    error_summary: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class BroadcastListResponse(BaseModel):
    items: list[BroadcastResponse]
    total: int
    page: int
    per_page: int


class BroadcastSendTestRequest(BaseModel):
    email: EmailStr | None = None


class BroadcastSendTestResponse(BaseModel):
    sent_to: str


class BroadcastRecipientItemResponse(BaseModel):
    id: int
    user_id: int | None
    email: str
    status: RecipientStatus
    error: str | None
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BroadcastRecipientListResponse(BaseModel):
    items: list[BroadcastRecipientItemResponse]
    total: int
    page: int
    per_page: int
