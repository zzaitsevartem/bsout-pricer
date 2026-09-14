from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, model_validator


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    tracked_product_id: int | None = None
    product_id: int | None = None
    type: str
    channel: str
    status: str
    title: str
    body: str
    old_price: Decimal | None = None
    new_price: Decimal | None = None
    error: str | None = None
    created_at: datetime
    sent_at: datetime | None = None
    read_at: datetime | None = None
    is_read: bool = False

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _set_is_read(self) -> "NotificationResponse":
        self.is_read = self.read_at is not None
        return self


class NotificationListResponse(BaseModel):
    results: list[NotificationResponse]
    total: int
    page: int
    per_page: int


class UnreadCountResponse(BaseModel):
    unread_count: int
