from datetime import datetime

from pydantic import BaseModel, Field


class VKAuthorizeResponse(BaseModel):
    authorize_url: str
    state: str
    expires_in: int


class VKCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=1024)
    state: str = Field(..., min_length=1, max_length=256)


class VKAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    created: bool


class TelegramLinkRequest(BaseModel):
    id: int
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    username: str | None = Field(None, max_length=255)
    photo_url: str | None = Field(None, max_length=1024)
    auth_date: int
    hash: str = Field(..., min_length=1, max_length=256)

    model_config = {"extra": "allow"}

    def signed_fields(self) -> dict[str, str]:
        raw = self.model_dump(exclude_unset=True)
        raw.pop("hash", None)
        return {key: str(value) for key, value in raw.items() if value is not None}


class TelegramNonceResponse(BaseModel):
    nonce: str
    expires_in: int
    bot_username: str | None = None


class IdentityResponse(BaseModel):
    provider: str
    provider_user_id: str
    display_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
