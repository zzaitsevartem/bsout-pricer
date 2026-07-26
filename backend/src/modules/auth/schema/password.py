from pydantic import BaseModel, EmailStr, Field, field_validator

from src.modules.auth.schema.auth import PASSWORD_TOO_LONG_MESSAGE
from src.modules.auth.service.auth import password_exceeds_bcrypt_limit

MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128
MAX_RESET_TOKEN_LENGTH = 512


def _validate_password_bytes(value: str) -> str:
    if password_exceeds_bcrypt_limit(value):
        raise ValueError(PASSWORD_TOO_LONG_MESSAGE)
    return value


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=MAX_RESET_TOKEN_LENGTH)
    new_password: str = Field(..., min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_bytes(cls, value: str) -> str:
        return _validate_password_bytes(value)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=1024)
    new_password: str = Field(..., min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_bytes(cls, value: str) -> str:
        return _validate_password_bytes(value)


class MessageResponse(BaseModel):
    detail: str
