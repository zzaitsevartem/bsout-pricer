import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.model.user import User
from src.modules.auth.model.verification import VerificationToken
from src.modules.auth.service.auth import (
    get_user_by_email,
    hash_password,
    verify_password,
)
from src.modules.auth.service.token_service import revoke_all_for_user
from src.modules.mail import get_mailer, password_reset_message

logger = logging.getLogger(__name__)

PURPOSE_PASSWORD_RESET = "password_reset"
RESET_TOKEN_TTL = timedelta(hours=1)
RESET_TOKEN_BYTES = 32

REASON_PASSWORD_RESET = "password_reset"
REASON_PASSWORD_CHANGE = "password_change"

INVALID_RESET_TOKEN_DETAIL = "Invalid or expired password reset token"
INVALID_CURRENT_PASSWORD_DETAIL = "Current password is incorrect"
RESET_REQUESTED_DETAIL = (
    "Если аккаунт с таким адресом существует, письмо со ссылкой для восстановления отправлено."
)


class PasswordResetError(Exception):
    def __init__(self, detail: str = INVALID_RESET_TOKEN_DETAIL) -> None:
        super().__init__(detail)
        self.detail = detail


class InvalidCurrentPasswordError(Exception):
    def __init__(self, detail: str = INVALID_CURRENT_PASSWORD_DETAIL) -> None:
        super().__init__(detail)
        self.detail = detail


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def generate_reset_token() -> str:
    return secrets.token_urlsafe(RESET_TOKEN_BYTES)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def invalidate_reset_tokens(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        update(VerificationToken)
        .where(
            VerificationToken.user_id == user_id,
            VerificationToken.purpose == PURPOSE_PASSWORD_RESET,
            VerificationToken.used_at.is_(None),
        )
        .values(used_at=_now())
        .execution_options(synchronize_session=False)
    )
    return result.rowcount or 0


async def request_password_reset(
    db: AsyncSession,
    email: str,
    requested_ip: str | None = None,
) -> str | None:
    normalized = email.strip().lower()
    user = await get_user_by_email(db, normalized)

    token = generate_reset_token()
    token_hash = hash_reset_token(token)

    if user is None or not user.is_active:
        await db.execute(
            select(VerificationToken.id).where(VerificationToken.token_hash == token_hash).limit(1)
        )
        await db.commit()
        return None

    await invalidate_reset_tokens(db, user.id)
    db.add(
        VerificationToken(
            user_id=user.id,
            purpose=PURPOSE_PASSWORD_RESET,
            token_hash=token_hash,
            expires_at=_now() + RESET_TOKEN_TTL,
            requested_ip=requested_ip,
        )
    )
    await db.commit()

    message = password_reset_message(token)
    await get_mailer().send(
        to=user.email,
        subject=message.subject,
        text=message.text,
        html=message.html,
    )
    return token


async def _load_usable_reset_token(db: AsyncSession, token: str) -> VerificationToken:
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token_hash == hash_reset_token(token),
            VerificationToken.purpose == PURPOSE_PASSWORD_RESET,
        )
    )
    stored = result.scalar_one_or_none()
    if stored is None:
        raise PasswordResetError()
    if stored.used_at is not None:
        raise PasswordResetError()
    if _aware(stored.expires_at) <= _now():
        raise PasswordResetError()
    return stored


async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> User:
    stored = await _load_usable_reset_token(db, token)

    user = (await db.execute(select(User).where(User.id == stored.user_id))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise PasswordResetError()

    user.password_hash = hash_password(new_password)
    stored.used_at = _now()
    await invalidate_reset_tokens(db, user.id)
    await revoke_all_for_user(db, user.id, REASON_PASSWORD_RESET)
    await db.commit()

    logger.info("password reset completed for user %s", user.id)
    return user


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> User:
    if not verify_password(current_password, user.password_hash):
        raise InvalidCurrentPasswordError()

    user.password_hash = hash_password(new_password)
    await invalidate_reset_tokens(db, user.id)
    await revoke_all_for_user(db, user.id, REASON_PASSWORD_CHANGE)
    await db.commit()

    logger.info("password changed for user %s", user.id)
    return user
