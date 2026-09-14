from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class EmailConfirmRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=512)


class EmailConfirmResponse(BaseModel):
    email_verified: bool
    email_verified_at: datetime


class EmailResendResponse(BaseModel):
    sent: bool
    expires_at: datetime


class EmailChangeRequest(BaseModel):
    new_email: EmailStr = Field(..., max_length=255)


class EmailChangeResponse(BaseModel):
    sent: bool
    expires_at: datetime
    new_email: str


class EmailChangeConfirmResponse(BaseModel):
    status: str
    email_verified_at: datetime | None = None


class EmailChangeCancelResponse(BaseModel):
    email: str


class EmailChangeFreezeResponse(BaseModel):
    frozen: bool
