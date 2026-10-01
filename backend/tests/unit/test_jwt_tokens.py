import pytest

from src.modules.auth.service.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
)

pytestmark = pytest.mark.unit


def test_access_token_roundtrip_carries_sub_and_type():
    payload = decode_token(create_access_token(42))
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_refresh_token_is_marked_refresh():
    payload = decode_token(create_refresh_token(7))
    assert payload is not None
    assert payload["type"] == "refresh"


def test_tampered_token_is_rejected():
    token = create_access_token(1)
    assert decode_token(token + "tamper") is None


def test_garbage_token_is_rejected():
    assert decode_token("not-a-jwt") is None
