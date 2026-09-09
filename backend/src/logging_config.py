import json
import logging
import re
import sys
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*)(bearer\s+)?[A-Za-z0-9._\-]+"),
    re.compile(
        r"(?i)\b(password|passwd|secret|api[_-]?key|token|hash)\b(\s*[:=]\s*)(\"?)([^\s\"',}&]+)"
    ),
    re.compile(r"(?i)([?&](?:token|nonce|code|state)=)[^&\s]+"),
    re.compile(r"\beyJ[A-Za-z0-9._\-]{10,}"),
)

REDACTED = "[скрыто]"

SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "password",
        "new_password",
        "current_password",
        "token",
        "access_token",
        "refresh_token",
        "reset_token",
        "idempotence_key",
        "secret",
        "api_key",
        "hash",
        "password_hash",
        "token_hash",
    }
)


def scrub(value: str) -> str:
    cleaned = value
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 4:
            cleaned = pattern.sub(
                lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{REDACTED}", cleaned
            )
        elif pattern.groups >= 2:
            cleaned = pattern.sub(lambda m: f"{m.group(1)}{REDACTED}", cleaned)
        else:
            cleaned = pattern.sub(REDACTED, cleaned)
    return cleaned


def scrub_mapping(payload: dict) -> dict:
    safe = {}
    for key, value in payload.items():
        if key.lower() in SENSITIVE_KEYS:
            safe[key] = REDACTED
        elif isinstance(value, dict):
            safe[key] = scrub_mapping(value)
        elif isinstance(value, str):
            safe[key] = scrub(value)
        else:
            safe[key] = value
    return safe


class SecretFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True
        record.msg = scrub(message)
        record.args = ()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = request_id_var.get()
        if request_id:
            payload["request_id"] = request_id
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(scrub_mapping(extra))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SecretFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    for noisy in ("sqlalchemy.engine", "sqlalchemy.pool", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
