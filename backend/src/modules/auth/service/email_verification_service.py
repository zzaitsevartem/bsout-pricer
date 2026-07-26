import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Protocol

from fastapi import Depends, HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.modules.auth.model.user import User
from src.modules.auth.model.verification import VerificationToken
from src.modules.auth.service.auth import get_user_by_id
from src.modules.cache.service.redis_cache import get_redis
from src.modules.shared import get_current_user

logger = logging.getLogger(__name__)

EMAIL_VERIFY_PURPOSE = "email_verify"
EMAIL_VERIFY_TTL_HOURS = 24
VERIFICATION_TOKEN_BYTES = 32

RESEND_MAX_ATTEMPTS = 3
RESEND_WINDOW_SECONDS = 3600
RESEND_QUOTA_PREFIX = "auth:email_verify:resend:"

REDIS_ERRORS = (RedisError, OSError)

INVALID_TOKEN_CODE = "invalid_token"
EXPIRED_TOKEN_CODE = "expired_token"
ALREADY_VERIFIED_CODE = "email_already_verified"
RATE_LIMITED_CODE = "resend_rate_limited"
MAIL_FAILED_CODE = "mail_send_failed"
EMAIL_NOT_VERIFIED_CODE = "email_not_verified"

INVALID_TOKEN_MESSAGE = "Ссылка подтверждения недействительна или уже использована."
EXPIRED_TOKEN_MESSAGE = "Срок действия ссылки истёк. Запросите письмо повторно."
ALREADY_VERIFIED_MESSAGE = "Адрес электронной почты уже подтверждён."
RATE_LIMITED_MESSAGE = "Слишком много писем с подтверждением. Попробуйте позже."
MAIL_FAILED_MESSAGE = "Не удалось отправить письмо. Попробуйте позже."
EMAIL_NOT_VERIFIED_MESSAGE = (
    "Подтвердите адрес электронной почты, чтобы оформить подписку и получать уведомления."
)

VERIFICATION_SUBJECT = "BScout: подтверждение адреса электронной почты"


class EmailVerificationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

    def as_detail(self) -> dict:
        return {"code": self.code, "message": self.message}


class VerificationMailer(Protocol):
    async def send_verification_email(
        self, *, to: str, link: str, expires_at: datetime
    ) -> None: ...


class ConsoleVerificationMailer:
    async def send_verification_email(self, *, to: str, link: str, expires_at: datetime) -> None:
        logger.info(
            "[mail:%s] to=%s subject=%s link=%s expires_at=%s",
            settings.mail_backend,
            to,
            VERIFICATION_SUBJECT,
            link,
            expires_at.isoformat(),
        )


def get_verification_mailer() -> VerificationMailer:
    return ConsoleVerificationMailer()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def hash_verification_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_verification_token() -> str:
    return secrets.token_urlsafe(VERIFICATION_TOKEN_BYTES)


def build_verification_link(raw_token: str) -> str:
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}/verify-email?token={raw_token}"


async def create_verification_token(
    db: AsyncSession,
    user_id: int,
    purpose: str = EMAIL_VERIFY_PURPOSE,
    ttl_hours: int = EMAIL_VERIFY_TTL_HOURS,
    requested_ip: str | None = None,
) -> tuple[str, VerificationToken]:
    raw_token = generate_verification_token()
    token = VerificationToken(
        user_id=user_id,
        purpose=purpose,
        token_hash=hash_verification_token(raw_token),
        expires_at=_now() + timedelta(hours=ttl_hours),
        requested_ip=requested_ip,
    )
    db.add(token)
    await db.flush()
    return raw_token, token


async def invalidate_pending_tokens(
    db: AsyncSession, user_id: int, purpose: str = EMAIL_VERIFY_PURPOSE
) -> None:
    await db.execute(
        update(VerificationToken)
        .where(
            VerificationToken.user_id == user_id,
            VerificationToken.purpose == purpose,
            VerificationToken.used_at.is_(None),
        )
        .values(used_at=func.now())
    )


async def issue_email_verification(
    db: AsyncSession,
    user: User,
    mailer: VerificationMailer | None = None,
    requested_ip: str | None = None,
    suppress_send_errors: bool = True,
) -> VerificationToken | None:
    sender = mailer if mailer is not None else get_verification_mailer()
    try:
        async with db.begin_nested():
            await invalidate_pending_tokens(db, user.id)
            raw_token, token = await create_verification_token(
                db, user.id, requested_ip=requested_ip
            )
    except Exception:
        logger.exception("failed to create email verification token for user %s", user.id)
        return None

    try:
        await sender.send_verification_email(
            to=user.email,
            link=build_verification_link(raw_token),
            expires_at=_aware(token.expires_at),
        )
    except Exception:
        logger.exception("failed to send verification email to user %s", user.id)
        if not suppress_send_errors:
            raise EmailVerificationError(
                MAIL_FAILED_CODE, MAIL_FAILED_MESSAGE, status.HTTP_502_BAD_GATEWAY
            )
    return token


async def confirm_email(db: AsyncSession, raw_token: str) -> User:
    result = await db.execute(
        select(VerificationToken)
        .where(
            VerificationToken.token_hash == hash_verification_token(raw_token),
            VerificationToken.purpose == EMAIL_VERIFY_PURPOSE,
        )
        .with_for_update()
    )
    token = result.scalar_one_or_none()
    if token is None or token.used_at is not None:
        raise EmailVerificationError(INVALID_TOKEN_CODE, INVALID_TOKEN_MESSAGE)
    if _aware(token.expires_at) <= _now():
        raise EmailVerificationError(EXPIRED_TOKEN_CODE, EXPIRED_TOKEN_MESSAGE)

    user = await get_user_by_id(db, token.user_id)
    if user is None or not user.is_active:
        raise EmailVerificationError(INVALID_TOKEN_CODE, INVALID_TOKEN_MESSAGE)

    token.used_at = _now()
    if user.email_verified_at is None:
        user.email_verified_at = _now()
    await db.flush()
    return user


async def consume_resend_quota(user_id: int) -> bool:
    key = f"{RESEND_QUOTA_PREFIX}{user_id}"
    try:
        redis = get_redis()
        attempts = int(await redis.incr(key))
        if attempts == 1:
            await redis.expire(key, RESEND_WINDOW_SECONDS)
    except REDIS_ERRORS as exc:
        logger.warning("email verification resend quota not enforced, redis unavailable: %s", exc)
        return True
    return attempts <= RESEND_MAX_ATTEMPTS


async def require_verified_email(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": EMAIL_NOT_VERIFIED_CODE, "message": EMAIL_NOT_VERIFIED_MESSAGE},
        )
    return current_user
