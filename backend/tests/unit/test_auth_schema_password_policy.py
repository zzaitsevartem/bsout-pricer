import pytest
from pydantic import ValidationError

from src.modules.auth.schema.auth import RegisterRequest
from src.modules.auth.schema.password import (
    MIN_PASSWORD_LENGTH,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
)


def test_registration_requires_twelve_character_password():
    common = {"email": "user@example.com", "full_name": "User"}

    with pytest.raises(ValidationError):
        RegisterRequest(**common, password="12345678901")

    request = RegisterRequest(**common, password="long-enough-pass")
    assert len(request.password) >= MIN_PASSWORD_LENGTH


@pytest.mark.parametrize(
    "schema,payload",
    [
        (PasswordResetConfirmRequest, {"token": "token", "new_password": "long-enough-pass"}),
        (
            PasswordChangeRequest,
            {"current_password": "existing", "new_password": "long-enough-pass"},
        ),
    ],
)
def test_password_reset_and_change_use_same_minimum(schema, payload):
    with pytest.raises(ValidationError):
        schema(**{**payload, "new_password": "12345678901"})

    request = schema(**payload)
    assert len(request.new_password) >= MIN_PASSWORD_LENGTH
