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
from src.modules.auth.service.auth import get_user_by_email, get_user_by_id
from src.modules.cache.service.redis_cache import get_redis
from src.modules.mail import MailNotConfiguredError, get_mailer
from src.modules.shared import get_current_user

logger = logging.getLogger(__name__)

EMAIL_VERIFY_PURPOSE = "email_verify"
EMAIL_CHANGE_PURPOSE = "email_change"
EMAIL_CHANGE_OLD_PURPOSE = "email_change_old"
EMAIL_CHANGE_NEW_PURPOSE = "email_change_new"
EMAIL_CHANGE_FREEZE_PURPOSE = "email_change_freeze"
EMAIL_VERIFY_TTL_HOURS = 24
VERIFICATION_TOKEN_BYTES = 32

RESEND_MAX_ATTEMPTS = 3
RESEND_WINDOW_SECONDS = 3600
RESEND_QUOTA_PREFIX = "auth:email_verify:resend:"
EMAIL_CHANGE_QUOTA_PREFIX = "auth:email_change:quota:"

EMAIL_CHANGE_SUBJECT = "BScout: смена адреса электронной почты"
EMAIL_CHANGE_PENDING_MESSAGE = "Запрос на смену адреса уже ожидает подтверждения."

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
        self,
        *,
        to: str,
        link: str,
        expires_at: datetime,
        text: str | None = None,
        html: str | None = None,
    ) -> None: ...


def build_verification_message(link: str, expires_at: datetime) -> tuple[str, str]:
    deadline = expires_at.strftime("%d.%m.%Y %H:%M UTC")
    text = (
        "Здравствуйте!\n\n"
        "Подтвердите адрес электронной почты в BScout, перейдя по ссылке:\n"
        f"{link}\n\n"
        f"Ссылка действует до {deadline} и может быть использована один раз.\n"
        "Если вы не регистрировались в BScout, просто проигнорируйте это письмо.\n"
    )
    html = (
        "<p>Здравствуйте!</p>"
        "<p>Подтвердите адрес электронной почты в BScout, перейдя по ссылке:<br>"
        f'<a href="{link}">{link}</a></p>'
        f"<p>Ссылка действует до {deadline} и может быть использована один раз.</p>"
        "<p>Если вы не регистрировались в BScout, просто проигнорируйте это письмо.</p>"
    )
    return text, html


class ConsoleVerificationMailer:
    async def send_verification_email(
        self,
        *,
        to: str,
        link: str,
        expires_at: datetime,
        text: str | None = None,
        html: str | None = None,
    ) -> None:
        logger.info(
            "verification email not delivered, mail backend is unusable: backend=%s to=%s",
            settings.mail_backend,
            to,
        )


class MailVerificationSender:
    def __init__(self, mailer=None, fallback: VerificationMailer | None = None) -> None:
        self._mailer = mailer
        self._fallback = fallback if fallback is not None else ConsoleVerificationMailer()

    async def send_verification_email(
        self,
        *,
        to: str,
        link: str,
        expires_at: datetime,
        text: str | None = None,
        html: str | None = None,
    ) -> None:
        text = text or build_verification_message(link, expires_at)[0]
        html = html or build_verification_message(link, expires_at)[1]
        try:
            mailer = self._mailer if self._mailer is not None else get_mailer()
            await mailer.send(to=to, subject=VERIFICATION_SUBJECT, text=text, html=html)
        except MailNotConfiguredError as exc:
            logger.error("verification email could not be sent: %s", exc)
            await self._fallback.send_verification_email(
                to=to, link=link, expires_at=expires_at
            )


def get_verification_mailer() -> VerificationMailer:
    return MailVerificationSender()


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


def build_verification_link(raw_token: str, purpose: str = EMAIL_VERIFY_PURPOSE) -> str:
    base = settings.frontend_base_url.rstrip("/")
    purpose_labels = {
        EMAIL_CHANGE_PURPOSE: "email_change",
        EMAIL_CHANGE_OLD_PURPOSE: "email_change_old",
        EMAIL_CHANGE_NEW_PURPOSE: "email_change_new",
        EMAIL_CHANGE_FREEZE_PURPOSE: "email_change_freeze",
    }
    label = purpose_labels.get(purpose)
    if label:
        return f"{base}/verify-email?token={raw_token}&purpose={label}"
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
        logger.warning(
            "email verification resend refused, quota cannot be enforced while redis is down: %s",
            exc,
        )
        return False
    return attempts <= RESEND_MAX_ATTEMPTS


async def require_verified_email(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": EMAIL_NOT_VERIFIED_CODE, "message": EMAIL_NOT_VERIFIED_MESSAGE},
        )
    return current_user


EMAIL_CHANGE_ALREADY_TAKEN_CODE = "email_already_taken"
EMAIL_CHANGE_SAME_CODE = "email_same"
EMAIL_CHANGE_PENDING_CODE = "email_change_pending"
EMAIL_CHANGE_RATE_LIMITED_CODE = "email_change_rate_limited"
EMAIL_CHANGE_INVALID_TOKEN_CODE = "invalid_token"
EMAIL_CHANGE_EXPIRED_TOKEN_CODE = "expired_token"
NO_PENDING_EMAIL_CODE = "no_pending_email"

EMAIL_CHANGE_ALREADY_TAKEN_MESSAGE = "Этот адрес электронной почты уже используется."
EMAIL_CHANGE_SAME_MESSAGE = "Новый адрес совпадает с текущим."
EMAIL_CHANGE_RATE_LIMITED_MESSAGE = "Слишком много запросов смены почты. Попробуйте позже."
NO_PENDING_EMAIL_MESSAGE = "Нет запроса на смену адреса электронной почты."


def build_email_change_message(
    link: str, new_email: str, freeze_link: str, expires_at: datetime
) -> tuple[str, str]:
    deadline = expires_at.strftime("%d.%m.%Y %H:%M UTC")
    text = (
        "Здравствуйте!\n\n"
        "Кто-то запросил смену адреса электронной почты в BScout на:\n"
        f"{new_email}\n\n"
        "ЕСЛИ ЭТО БЫЛИ ВЫ — перейдите по ссылке, чтобы подтвердить смену:\n"
        f"{link}\n\n"
        f"Ссылка действует до {deadline} и может быть использована один раз.\n\n"
        "ЕСЛИ ЭТО БЫЛИ НЕ ВЫ — кто-то пытается получить контроль над аккаунтом.\n"
        "Нажмите на ссылку «Я этого не делал», чтобы немедленно заморозить аккаунт:\n"
        f"{freeze_link}\n"
    )
    html = (
        "<p>Здравствуйте!</p>"
        "<p>Кто-то запросил смену адреса электронной почты в BScout на "
        f"<strong>{new_email}</strong>.</p>"
        '<p><strong>Если это были вы</strong>, подтвердите смену:</p>'
        f'<p><a href="{link}" style="display:inline-block;padding:10px 16px;'
        'background:#2a2a2a;color:#ffffff;border-radius:8px;'
        'text-decoration:none;">Подтвердить смену</a></p>'
        f"<p>Ссылка действует до {deadline} и может быть использована один раз.</p>"
        '<p><strong>Если это были не вы</strong> — заморозьте аккаунт:</p>'
        '<p><a href="'
        f'{freeze_link}'
        '" style="color:#b91c1c;">Я этого не делал — заморозить аккаунт</a></p>'
        "<p>Это защита от попытки взлома: если вы не инициировали смену, "
        "аккаунт будет заблокирован до выяснения.</p>"
    )
    return text, html


def build_email_change_new_message(link: str, expires_at: datetime) -> tuple[str, str]:
    deadline = expires_at.strftime("%d.%m.%Y %H:%M UTC")
    text = (
        "Здравствуйте!\n\n"
        "Вы подтвердили смену адреса на старой почте. Остался последний шаг.\n\n"
        "Чтобы завершить смену, перейдите по ссылке на этот новый адрес:\n"
        f"{link}\n\n"
        f"Ссылка действует до {deadline} и может быть использована один раз.\n"
    )
    html = (
        "<p>Здравствуйте!</p>"
        "<p>Вы подтвердили смену адреса на старой почте. Остался последний шаг.</p>"
        "<p>Чтобы завершить смену, перейдите по ссылке:</p>"
        f'<p><a href="{link}" style="display:inline-block;padding:10px 16px;'
        'background:#2a2a2a;color:#ffffff;border-radius:8px;'
        'text-decoration:none;">Подтвердить смену</a></p>'
        f"<p>Ссылка действует до {deadline} и может быть использована один раз.</p>"
    )
    return text, html


async def consume_email_change_quota(user_id: int, max_attempts: int = 3) -> bool:
    key = f"{EMAIL_CHANGE_QUOTA_PREFIX}{user_id}"
    try:
        redis = get_redis()
        attempts = int(await redis.incr(key))
        if attempts == 1:
            await redis.expire(key, RESEND_WINDOW_SECONDS)
    except REDIS_ERRORS as exc:
        logger.warning(
            "email change quota refused, cannot be enforced while redis is down: %s", exc
        )
        return False
    return attempts <= max_attempts


async def request_email_change(
    db: AsyncSession,
    user: User,
    new_email: str,
    mailer: VerificationMailer | None = None,
    requested_ip: str | None = None,
) -> VerificationToken:
    normalized = new_email.strip().lower()
    if normalized == user.email.strip().lower():
        raise EmailVerificationError(EMAIL_CHANGE_SAME_CODE, EMAIL_CHANGE_SAME_MESSAGE)

    existing = await get_user_by_email(db, normalized)
    if existing is not None and existing.id != user.id:
        raise EmailVerificationError(
            EMAIL_CHANGE_ALREADY_TAKEN_CODE, EMAIL_CHANGE_ALREADY_TAKEN_MESSAGE
        )

    if user.pending_email is not None:
        raise EmailVerificationError(EMAIL_CHANGE_PENDING_CODE, EMAIL_CHANGE_PENDING_MESSAGE)

    if not await consume_email_change_quota(user.id):
        raise EmailVerificationError(
            EMAIL_CHANGE_RATE_LIMITED_CODE,
            EMAIL_CHANGE_RATE_LIMITED_MESSAGE,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    sender = mailer if mailer is not None else get_verification_mailer()
    try:
        async with db.begin_nested():
            await invalidate_pending_tokens(db, user.id, purpose=EMAIL_CHANGE_OLD_PURPOSE)
            await invalidate_pending_tokens(db, user.id, purpose=EMAIL_CHANGE_NEW_PURPOSE)
            raw_token, token = await create_verification_token(
                db, user.id, purpose=EMAIL_CHANGE_OLD_PURPOSE, requested_ip=requested_ip
            )
            raw_freeze, _freeze_token = await create_verification_token(
                db, user.id, purpose=EMAIL_CHANGE_FREEZE_PURPOSE, requested_ip=requested_ip
            )
    except Exception:
        logger.exception("failed to create email change token for user %s", user.id)
        raise EmailVerificationError(
            EMAIL_CHANGE_INVALID_TOKEN_CODE, "Не удалось создать запрос смены почты."
        )

    confirm_link = build_verification_link(raw_token, purpose=EMAIL_CHANGE_OLD_PURPOSE)
    freeze_link = build_verification_link(raw_freeze, purpose=EMAIL_CHANGE_FREEZE_PURPOSE)
    text, html = build_email_change_message(
        confirm_link, normalized, freeze_link, _aware(token.expires_at)
    )
    try:
        await sender.send_verification_email(
            to=user.email,
            link=confirm_link,
            expires_at=_aware(token.expires_at),
            text=text,
            html=html,
        )
    except Exception:
        logger.exception("failed to send email change mail to %s", user.email)

    user.pending_email = normalized
    user.email_change_old_confirmed_at = None
    await db.flush()
    return token


async def confirm_email_change_old(
    db: AsyncSession,
    raw_token: str,
    mailer: VerificationMailer | None = None,
    requested_ip: str | None = None,
) -> User:
    token = await _consume_change_token(db, raw_token, EMAIL_CHANGE_OLD_PURPOSE)
    user = await get_user_by_id(db, token.user_id)
    if user is None or not user.is_active:
        raise EmailVerificationError(INVALID_TOKEN_CODE, INVALID_TOKEN_MESSAGE)
    if user.pending_email is None:
        raise EmailVerificationError(NO_PENDING_EMAIL_CODE, NO_PENDING_EMAIL_MESSAGE)

    user.email_change_old_confirmed_at = _now()

    sender = mailer if mailer is not None else get_verification_mailer()
    try:
        async with db.begin_nested():
            await invalidate_pending_tokens(db, user.id, purpose=EMAIL_CHANGE_NEW_PURPOSE)
            raw_new, new_token = await create_verification_token(
                db, user.id, purpose=EMAIL_CHANGE_NEW_PURPOSE, requested_ip=requested_ip
            )
    except Exception:
        logger.exception("failed to issue email change second step for user %s", user.id)
    else:
        link = build_verification_link(raw_new, purpose=EMAIL_CHANGE_NEW_PURPOSE)
        text, html = build_email_change_new_message(
            link, _aware(new_token.expires_at)
        )
        try:
            await sender.send_verification_email(
                to=user.pending_email,
                link=link,
                expires_at=_aware(new_token.expires_at),
                text=text,
                html=html,
            )
        except Exception:
            logger.exception(
                "failed to send email change new mail to %s", user.pending_email
            )
    await db.flush()
    return user


async def confirm_email_change_new(db: AsyncSession, raw_token: str) -> User:
    token = await _consume_change_token(db, raw_token, EMAIL_CHANGE_NEW_PURPOSE)
    user = await get_user_by_id(db, token.user_id)
    if user is None or not user.is_active:
        raise EmailVerificationError(INVALID_TOKEN_CODE, INVALID_TOKEN_MESSAGE)
    if user.pending_email is None:
        raise EmailVerificationError(NO_PENDING_EMAIL_CODE, NO_PENDING_EMAIL_MESSAGE)
    if user.email_change_old_confirmed_at is None:
        raise EmailVerificationError(
            EMAIL_CHANGE_INVALID_TOKEN_CODE,
            "Сначала подтвердите смену на старой почте.",
        )

    user.email = user.pending_email
    user.email_verified_at = _now()
    user.pending_email = None
    user.email_change_old_confirmed_at = None
    await db.flush()
    return user


async def freeze_email_change(db: AsyncSession, raw_token: str) -> User:
    token = await _consume_change_token(db, raw_token, EMAIL_CHANGE_FREEZE_PURPOSE)
    user = await get_user_by_id(db, token.user_id)
    if user is None:
        raise EmailVerificationError(INVALID_TOKEN_CODE, INVALID_TOKEN_MESSAGE)

    user.is_active = False
    user.pending_email = None
    user.email_change_old_confirmed_at = None
    await db.flush()
    return user


async def _consume_change_token(
    db: AsyncSession, raw_token: str, purpose: str
) -> VerificationToken:
    result = await db.execute(
        select(VerificationToken)
        .where(
            VerificationToken.token_hash == hash_verification_token(raw_token),
            VerificationToken.purpose == purpose,
        )
        .with_for_update()
    )
    token = result.scalar_one_or_none()
    if token is None or token.used_at is not None:
        raise EmailVerificationError(INVALID_TOKEN_CODE, INVALID_TOKEN_MESSAGE)
    if _aware(token.expires_at) <= _now():
        raise EmailVerificationError(EXPIRED_TOKEN_CODE, EXPIRED_TOKEN_MESSAGE)
    token.used_at = _now()
    await db.flush()
    return token


async def cancel_email_change(db: AsyncSession, user: User) -> User:
    if user.pending_email is None:
        raise EmailVerificationError(NO_PENDING_EMAIL_CODE, NO_PENDING_EMAIL_MESSAGE)
    user.pending_email = None
    user.email_change_old_confirmed_at = None
    await db.flush()
    return user
