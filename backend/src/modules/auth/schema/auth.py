from pydantic import BaseModel, EmailStr, Field, field_validator

from src.modules.auth.service.auth import MAX_PASSWORD_BYTES, password_exceeds_bcrypt_limit

PASSWORD_TOO_LONG_MESSAGE = (
    f"password must not exceed {MAX_PASSWORD_BYTES} bytes in utf-8 "
    "(non-latin characters take more than one byte)"
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=20)
    company: str | None = Field(None, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if password_exceeds_bcrypt_limit(value):
            raise ValueError(PASSWORD_TOO_LONG_MESSAGE)
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
