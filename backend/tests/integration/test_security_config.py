import logging

import pytest

from src.config import Settings
from src.modules.auth.service import security
from src.modules.auth.service.security import (
    DEFAULT_JWT_SECRET,
    MIN_JWT_SECRET_LENGTH,
    InsecureConfigurationError,
    WeakCredentialsError,
    collect_security_problems,
    validate_admin_credentials,
    validate_security_settings,
)

pytestmark = pytest.mark.integration

STRONG_SECRET = "a" * MIN_JWT_SECRET_LENGTH


def build_settings(secret: str, debug: bool) -> Settings:
    return Settings(jwt_secret_key=secret, debug=debug)


def test_default_secret_outside_debug_refuses_to_start():
    config = build_settings(DEFAULT_JWT_SECRET, debug=False)

    with pytest.raises(InsecureConfigurationError) as exc_info:
        validate_security_settings(config)

    assert "jwt_secret_key" in str(exc_info.value)
    assert "default" in str(exc_info.value)


def test_default_secret_in_debug_only_warns(caplog):
    config = build_settings(DEFAULT_JWT_SECRET, debug=True)

    with caplog.at_level(logging.WARNING, logger=security.logger.name):
        problems = validate_security_settings(config)

    assert len(problems) == 1
    assert any("jwt_secret_key" in record.getMessage() for record in caplog.records)


def test_strong_secret_passes_quietly(caplog):
    config = build_settings(STRONG_SECRET, debug=False)

    with caplog.at_level(logging.WARNING, logger=security.logger.name):
        problems = validate_security_settings(config)

    assert problems == []
    assert caplog.records == []


def test_short_secret_outside_debug_refuses_to_start():
    config = build_settings("x" * (MIN_JWT_SECRET_LENGTH - 1), debug=False)

    with pytest.raises(InsecureConfigurationError) as exc_info:
        validate_security_settings(config)

    assert str(MIN_JWT_SECRET_LENGTH) in str(exc_info.value)


def test_secret_of_exactly_the_minimum_length_is_accepted():
    assert collect_security_problems(build_settings(STRONG_SECRET, debug=False)) == []


def test_short_secret_in_debug_only_warns():
    config = build_settings("short", debug=True)

    assert validate_security_settings(config) != []


def test_empty_secret_is_reported_as_too_short():
    problems = collect_security_problems(build_settings("", debug=True))

    assert len(problems) == 1
    assert "shorter" in problems[0]


def test_default_secret_is_reported_as_a_default_not_as_too_short():
    problems = collect_security_problems(build_settings(DEFAULT_JWT_SECRET, debug=True))

    assert problems == ["jwt_secret_key still holds the built-in default value"]


def test_validation_falls_back_to_the_module_settings(monkeypatch):
    monkeypatch.setattr(security, "settings", build_settings(DEFAULT_JWT_SECRET, debug=False))

    with pytest.raises(InsecureConfigurationError):
        validate_security_settings()


def test_the_guarded_default_matches_the_one_shipped_in_config():
    assert Settings.model_fields["jwt_secret_key"].default == DEFAULT_JWT_SECRET


def test_admin_credentials_accept_a_valid_trio():
    credentials = validate_admin_credentials(
        email="Root@Example.com", password="s3cret-pass", full_name="Root"
    )

    assert credentials.password == "s3cret-pass"
    assert credentials.full_name == "Root"


@pytest.mark.parametrize("password", ["", "12345"])
def test_admin_password_must_satisfy_the_registration_policy(password):
    with pytest.raises(WeakCredentialsError) as exc_info:
        validate_admin_credentials(email="root@example.com", password=password, full_name="Root")

    assert "password" in str(exc_info.value)


def test_admin_password_longer_than_the_registration_maximum_is_rejected():
    with pytest.raises(WeakCredentialsError):
        validate_admin_credentials(email="root@example.com", password="p" * 129, full_name="Root")


def test_admin_email_must_be_a_real_address():
    with pytest.raises(WeakCredentialsError) as exc_info:
        validate_admin_credentials(email="not-an-email", password="s3cret-pass", full_name="Root")

    assert "email" in str(exc_info.value)


def test_admin_full_name_cannot_be_blank():
    with pytest.raises(WeakCredentialsError) as exc_info:
        validate_admin_credentials(email="root@example.com", password="s3cret-pass", full_name="")

    assert "full_name" in str(exc_info.value)
