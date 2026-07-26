from datetime import datetime

from pydantic import BaseModel, Field


class EmailConfirmRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=512)


class EmailConfirmResponse(BaseModel):
    email_verified: bool
    email_verified_at: datetime


class EmailResendResponse(BaseModel):
    sent: bool
    expires_at: datetime
