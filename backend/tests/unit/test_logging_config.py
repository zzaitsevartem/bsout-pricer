import json
import logging

from src.logging_config import (
    JsonFormatter,
    SecretFilter,
    request_id_var,
    scrub,
    scrub_mapping,
)


def _record(message: str, **extra) -> logging.LogRecord:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, message, (), None)
    if extra:
        record.extra_fields = extra
    return record


def test_formatter_emits_valid_json_with_expected_fields():
    payload = json.loads(JsonFormatter().format(_record("привет")))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "test"
    assert payload["message"] == "привет"
    assert payload["ts"]


def test_request_id_lands_in_every_record():
    token = request_id_var.set("req-123")
    try:
        payload = json.loads(JsonFormatter().format(_record("работа")))
    finally:
        request_id_var.reset(token)

    assert payload["request_id"] == "req-123"


def test_authorization_header_is_never_logged():
    cleaned = scrub("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature")

    assert "eyJhbGciOiJIUzI1NiJ9" not in cleaned
    assert "скрыто" in cleaned


def test_password_reset_link_token_is_stripped():
    cleaned = scrub("https://bscout.ru/reset?token=SuperSecretResetToken123&utm=mail")

    assert "SuperSecretResetToken123" not in cleaned
    assert "utm=mail" in cleaned


def test_jwt_anywhere_in_message_is_stripped():
    cleaned = scrub("выдан токен eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9abcdef для пользователя 5")

    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9abcdef" not in cleaned
    assert "для пользователя 5" in cleaned


def test_password_and_secret_values_are_stripped():
    cleaned = scrub("login failed password=hunter2 api_key=abcdef123")

    assert "hunter2" not in cleaned
    assert "abcdef123" not in cleaned


def test_sensitive_keys_in_extra_fields_are_redacted():
    safe = scrub_mapping(
        {
            "user_id": 7,
            "password": "hunter2",
            "refresh_token": "rt-secret",
            "nested": {"token_hash": "deadbeef", "keep": "видно"},
        }
    )

    assert safe["user_id"] == 7
    assert "hunter2" not in json.dumps(safe, ensure_ascii=False)
    assert "rt-secret" not in json.dumps(safe, ensure_ascii=False)
    assert "deadbeef" not in json.dumps(safe, ensure_ascii=False)
    assert safe["nested"]["keep"] == "видно"


def test_secret_filter_rewrites_the_record_message():
    record = _record("reset link https://bscout.ru/reset?token=LeakedValue")

    assert SecretFilter().filter(record) is True
    assert "LeakedValue" not in record.getMessage()
