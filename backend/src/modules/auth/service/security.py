import logging

from pydantic import ValidationError

from src.config import settings
from src.modules.auth.schema.auth import RegisterRequest

logger = logging.getLogger(__name__)

DEFAULT_JWT_SECRET = "change-me-to-a-random-secret"
MIN_JWT_SECRET_LENGTH = 32


class InsecureConfigurationError(RuntimeError):
    pass


class WeakCredentialsError(ValueError):
    pass


def collect_security_problems(config=None) -> list[str]:
    config = settings if config is None else config
    problems: list[str] = []
    secret = getattr(config, "jwt_secret_key", "") or ""
    if secret == DEFAULT_JWT_SECRET:
        problems.append("jwt_secret_key still holds the built-in default value")
    elif len(secret) < MIN_JWT_SECRET_LENGTH:
        problems.append(f"jwt_secret_key is shorter than {MIN_JWT_SECRET_LENGTH} characters")
    return problems


def validate_security_settings(config=None) -> list[str]:
    config = settings if config is None else config
    problems = collect_security_problems(config)
    if not problems:
        return []
    if getattr(config, "debug", False):
        for problem in problems:
            logger.warning("insecure configuration tolerated because debug is on: %s", problem)
        return problems
    raise InsecureConfigurationError(
        "refusing to start with insecure configuration: "
        + "; ".join(problems)
        + "; set a random JWT_SECRET_KEY of at least "
        + f"{MIN_JWT_SECRET_LENGTH} characters"
    )


def validate_admin_credentials(email: str, password: str, full_name: str) -> RegisterRequest:
    try:
        return RegisterRequest(email=email, password=password, full_name=full_name)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        raise WeakCredentialsError(details) from exc
