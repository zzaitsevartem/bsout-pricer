import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from urllib.parse import urlencode

import httpx
from fastapi import status
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.modules.auth.model.user import User
from src.modules.auth.model.verification import UserIdentity
from src.modules.auth.service.auth import (
    get_user_by_email,
    get_user_by_id,
    grant_trial_subscription,
    hash_password,
)
from src.modules.cache.service.redis_cache import get_redis

logger = logging.getLogger(__name__)

VK_PROVIDER = "vk"
TELEGRAM_PROVIDER = "telegram"

VK_STATE_PREFIX = "auth:vk:state:"
VK_STATE_TTL_SECONDS = 600
VK_API_VERSION = "5.199"
VK_AUTHORIZE_ENDPOINT = "https://oauth.vk.com/authorize"
VK_TOKEN_ENDPOINT = "https://oauth.vk.com/access_token"
VK_USERS_ENDPOINT = "https://api.vk.com/method/users.get"
VK_SCOPE = "email"
VK_HTTP_TIMEOUT = 10.0

TELEGRAM_AUTH_MAX_AGE_SECONDS = 120
TELEGRAM_CLOCK_SKEW_SECONDS = 60
TELEGRAM_USED_PREFIX = "auth:telegram:used:"
TELEGRAM_NONCE_PREFIX = "auth:telegram:nonce:"
TELEGRAM_NONCE_TTL_SECONDS = 600

UNUSABLE_PASSWORD_MARKER = "." * 31

REDIS_ERRORS = (RedisError, OSError)

VK_NOT_CONFIGURED_CODE = "vk_not_configured"
VK_STATE_UNAVAILABLE_CODE = "vk_state_unavailable"
INVALID_STATE_CODE = "invalid_state"
VK_EMAIL_REQUIRED_CODE = "vk_email_required"
VK_EMAIL_REGISTERED_CODE = "vk_email_registered"
VK_IDENTITY_TAKEN_CODE = "vk_identity_taken"
VK_ALREADY_LINKED_CODE = "vk_already_linked"
VK_NOT_LINKED_CODE = "vk_not_linked"
VK_EXCHANGE_FAILED_CODE = "vk_exchange_failed"
VK_ACCOUNT_DISABLED_CODE = "vk_account_disabled"
LAST_LOGIN_METHOD_CODE = "last_login_method"

TELEGRAM_NOT_CONFIGURED_CODE = "telegram_not_configured"
TELEGRAM_BAD_SIGNATURE_CODE = "telegram_bad_signature"
TELEGRAM_STALE_AUTH_CODE = "telegram_stale_auth"
TELEGRAM_REPLAYED_CODE = "telegram_replayed_auth"
TELEGRAM_INVALID_NONCE_CODE = "telegram_invalid_nonce"
TELEGRAM_UNAVAILABLE_CODE = "telegram_link_unavailable"
TELEGRAM_IDENTITY_TAKEN_CODE = "telegram_identity_taken"
TELEGRAM_ALREADY_LINKED_CODE = "telegram_already_linked"
TELEGRAM_NOT_LINKED_CODE = "telegram_not_linked"

VK_NOT_CONFIGURED_MESSAGE = "Вход через ВКонтакте не настроен на сервере."
VK_STATE_UNAVAILABLE_MESSAGE = "Вход через ВКонтакте временно недоступен. Попробуйте позже."
INVALID_STATE_MESSAGE = "Сессия авторизации устарела или недействительна. Начните вход заново."
VK_EMAIL_REQUIRED_MESSAGE = (
    "ВКонтакте не передал адрес электронной почты. "
    "Разрешите доступ к почте или зарегистрируйтесь обычным способом."
)
VK_EMAIL_REGISTERED_MESSAGE = (
    "Аккаунт с таким адресом уже зарегистрирован. "
    "Войдите обычным способом и привяжите ВКонтакте в личном кабинете."
)
VK_IDENTITY_TAKEN_MESSAGE = "Этот профиль ВКонтакте уже привязан к другому аккаунту."
VK_ALREADY_LINKED_MESSAGE = (
    "К аккаунту уже привязан другой профиль ВКонтакте. Сначала отвяжите его."
)
VK_NOT_LINKED_MESSAGE = "Профиль ВКонтакте не привязан к аккаунту."
VK_EXCHANGE_FAILED_MESSAGE = "ВКонтакте отклонил авторизацию. Попробуйте войти заново."
VK_ACCOUNT_DISABLED_MESSAGE = "Аккаунт отключён."
LAST_LOGIN_METHOD_MESSAGE = (
    "Это единственный способ входа в аккаунт. Задайте пароль, прежде чем отвязывать ВКонтакте."
)

TELEGRAM_NOT_CONFIGURED_MESSAGE = "Привязка Телеграма не настроена на сервере."
TELEGRAM_BAD_SIGNATURE_MESSAGE = "Подпись данных Телеграма недействительна."
TELEGRAM_STALE_AUTH_MESSAGE = "Данные авторизации Телеграма устарели. Повторите вход через виджет."
TELEGRAM_REPLAYED_MESSAGE = (
    "Эти данные Телеграма уже были использованы. Повторите вход через виджет."
)
TELEGRAM_INVALID_NONCE_MESSAGE = (
    "Одноразовый код привязки Телеграма недействителен. Начните привязку заново."
)
TELEGRAM_UNAVAILABLE_MESSAGE = "Привязка Телеграма временно недоступна. Попробуйте позже."
TELEGRAM_IDENTITY_TAKEN_MESSAGE = "Этот аккаунт Телеграма уже привязан к другому пользователю."
TELEGRAM_ALREADY_LINKED_MESSAGE = (
    "К аккаунту уже привязан другой Телеграм. Сначала отвяжите текущий."
)
TELEGRAM_NOT_LINKED_MESSAGE = "Телеграм не привязан к аккаунту."


class OAuthError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

    def as_detail(self) -> dict:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class VKProfile:
    provider_user_id: str
    email: str | None = None
    display_name: str | None = None


class VKClient(Protocol):
    async def exchange_code(self, code: str) -> VKProfile: ...


class HttpVKClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        timeout: float = VK_HTTP_TIMEOUT,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.timeout = timeout

    async def exchange_code(self, code: str) -> VKProfile:
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                token_response = await http.get(
                    VK_TOKEN_ENDPOINT,
                    params={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                        "code": code,
                    },
                )
                payload = token_response.json()
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning("vk token exchange failed: %s", exc)
                raise OAuthError(VK_EXCHANGE_FAILED_CODE, VK_EXCHANGE_FAILED_MESSAGE)

            access_token = payload.get("access_token")
            provider_user_id = payload.get("user_id")
            if not access_token or provider_user_id is None:
                logger.warning("vk token exchange rejected: %s", payload.get("error"))
                raise OAuthError(VK_EXCHANGE_FAILED_CODE, VK_EXCHANGE_FAILED_MESSAGE)

            display_name = None
            try:
                users_response = await http.get(
                    VK_USERS_ENDPOINT,
                    params={
                        "access_token": access_token,
                        "user_ids": str(provider_user_id),
                        "v": VK_API_VERSION,
                    },
                )
                items = users_response.json().get("response") or []
                if items:
                    first = items[0].get("first_name") or ""
                    last = items[0].get("last_name") or ""
                    display_name = f"{first} {last}".strip() or None
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning("vk profile lookup failed: %s", exc)

        return VKProfile(
            provider_user_id=str(provider_user_id),
            email=payload.get("email"),
            display_name=display_name,
        )


def vk_is_configured() -> bool:
    return bool(settings.vk_client_id and settings.vk_client_secret and settings.vk_redirect_uri)


def ensure_vk_configured() -> None:
    if not vk_is_configured():
        raise OAuthError(
            VK_NOT_CONFIGURED_CODE,
            VK_NOT_CONFIGURED_MESSAGE,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def get_vk_client() -> VKClient:
    ensure_vk_configured()
    return HttpVKClient(
        client_id=settings.vk_client_id,
        client_secret=settings.vk_client_secret,
        redirect_uri=settings.vk_redirect_uri,
    )


def build_vk_authorize_url(state: str) -> str:
    params = {
        "client_id": settings.vk_client_id,
        "redirect_uri": settings.vk_redirect_uri,
        "display": "page",
        "scope": VK_SCOPE,
        "response_type": "code",
        "v": VK_API_VERSION,
        "state": state,
    }
    return f"{VK_AUTHORIZE_ENDPOINT}?{urlencode(params)}"


async def create_vk_state(purpose: str = "login", user_id: int | None = None) -> str:
    if purpose not in ("login", "link"):
        raise OAuthError(INVALID_STATE_CODE, INVALID_STATE_MESSAGE, status.HTTP_400_BAD_REQUEST)
    state = secrets.token_urlsafe(32)
    payload = json.dumps({"purpose": purpose, "user_id": user_id})
    try:
        redis = get_redis()
        await redis.set(f"{VK_STATE_PREFIX}{state}", payload, ex=VK_STATE_TTL_SECONDS)
    except REDIS_ERRORS as exc:
        logger.warning("vk state could not be stored, redis unavailable: %s", exc)
        raise OAuthError(
            VK_STATE_UNAVAILABLE_CODE,
            VK_STATE_UNAVAILABLE_MESSAGE,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return state


async def consume_vk_state(state: str) -> dict | None:
    if not state:
        return None
    key = f"{VK_STATE_PREFIX}{state}"
    try:
        redis = get_redis()
        raw = await redis.getdel(key)
    except REDIS_ERRORS as exc:
        logger.warning("vk state could not be verified, redis unavailable: %s", exc)
        return None
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "ignore")
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def require_vk_state(payload: dict | None, purpose: str, user_id: int | None = None) -> None:
    if not payload or payload.get("purpose") != purpose:
        raise OAuthError(INVALID_STATE_CODE, INVALID_STATE_MESSAGE, status.HTTP_400_BAD_REQUEST)
    if purpose == "link" and payload.get("user_id") != user_id:
        raise OAuthError(INVALID_STATE_CODE, INVALID_STATE_MESSAGE, status.HTTP_400_BAD_REQUEST)


def set_unusable_password() -> str:
    placeholder = hash_password(secrets.token_urlsafe(24))
    keep = len(placeholder) - len(UNUSABLE_PASSWORD_MARKER)
    return placeholder[:keep] + UNUSABLE_PASSWORD_MARKER


def user_has_usable_password(user: User) -> bool:
    return not (user.password_hash or "").endswith(UNUSABLE_PASSWORD_MARKER)


async def get_identity(
    db: AsyncSession, provider: str, provider_user_id: str
) -> UserIdentity | None:
    result = await db.execute(
        select(UserIdentity).where(
            UserIdentity.provider == provider,
            UserIdentity.provider_user_id == provider_user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_user_identity(db: AsyncSession, user_id: int, provider: str) -> UserIdentity | None:
    result = await db.execute(
        select(UserIdentity).where(
            UserIdentity.user_id == user_id, UserIdentity.provider == provider
        )
    )
    return result.scalar_one_or_none()


async def list_identities(db: AsyncSession, user_id: int) -> list[UserIdentity]:
    result = await db.execute(select(UserIdentity).where(UserIdentity.user_id == user_id))
    return list(result.scalars().all())


async def login_or_register_vk(db: AsyncSession, profile: VKProfile) -> tuple[User, bool]:
    identity = await get_identity(db, VK_PROVIDER, profile.provider_user_id)
    if identity is not None:
        user = await get_user_by_id(db, identity.user_id)
        if user is None or not user.is_active:
            raise OAuthError(
                VK_ACCOUNT_DISABLED_CODE, VK_ACCOUNT_DISABLED_MESSAGE, status.HTTP_403_FORBIDDEN
            )
        if profile.display_name and identity.display_name != profile.display_name:
            identity.display_name = profile.display_name
            await db.flush()
        return user, False

    if not profile.email:
        raise OAuthError(
            VK_EMAIL_REQUIRED_CODE, VK_EMAIL_REQUIRED_MESSAGE, status.HTTP_400_BAD_REQUEST
        )

    existing = await get_user_by_email(db, profile.email)
    if existing is not None:
        raise OAuthError(
            VK_EMAIL_REGISTERED_CODE, VK_EMAIL_REGISTERED_MESSAGE, status.HTTP_409_CONFLICT
        )

    user = User(
        email=profile.email,
        password_hash=set_unusable_password(),
        full_name=profile.display_name or profile.email.split("@")[0],
        is_active=True,
        email_verified_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()

    db.add(
        UserIdentity(
            user_id=user.id,
            provider=VK_PROVIDER,
            provider_user_id=profile.provider_user_id,
            display_name=profile.display_name,
        )
    )
    await db.flush()

    try:
        async with db.begin_nested():
            await grant_trial_subscription(db, user)
    except Exception:
        logger.exception("failed to grant trial subscription for vk user %s", user.id)

    return user, True


async def link_identity(
    db: AsyncSession,
    user: User,
    provider: str,
    provider_user_id: str,
    display_name: str | None,
    taken_code: str,
    taken_message: str,
    already_linked_code: str,
    already_linked_message: str,
) -> UserIdentity:
    existing = await get_identity(db, provider, provider_user_id)
    if existing is not None:
        if existing.user_id != user.id:
            raise OAuthError(taken_code, taken_message, status.HTTP_409_CONFLICT)
        if display_name and existing.display_name != display_name:
            existing.display_name = display_name
            await db.flush()
        return existing

    mine = await get_user_identity(db, user.id, provider)
    if mine is not None:
        raise OAuthError(already_linked_code, already_linked_message, status.HTTP_409_CONFLICT)

    identity = UserIdentity(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        display_name=display_name,
    )
    db.add(identity)
    await db.flush()
    return identity


async def link_vk_identity(db: AsyncSession, user: User, profile: VKProfile) -> UserIdentity:
    return await link_identity(
        db,
        user,
        VK_PROVIDER,
        profile.provider_user_id,
        profile.display_name,
        VK_IDENTITY_TAKEN_CODE,
        VK_IDENTITY_TAKEN_MESSAGE,
        VK_ALREADY_LINKED_CODE,
        VK_ALREADY_LINKED_MESSAGE,
    )


async def unlink_vk_identity(db: AsyncSession, user: User) -> None:
    identity = await get_user_identity(db, user.id, VK_PROVIDER)
    if identity is None:
        raise OAuthError(VK_NOT_LINKED_CODE, VK_NOT_LINKED_MESSAGE, status.HTTP_404_NOT_FOUND)
    if not user_has_usable_password(user):
        raise OAuthError(
            LAST_LOGIN_METHOD_CODE, LAST_LOGIN_METHOD_MESSAGE, status.HTTP_409_CONFLICT
        )
    await db.delete(identity)
    await db.flush()


def telegram_display_name(fields: dict[str, str]) -> str | None:
    username = fields.get("username")
    if username:
        return username[:255]
    parts = [fields.get("first_name") or "", fields.get("last_name") or ""]
    combined = " ".join(part for part in parts if part).strip()
    return combined[:255] or None


def verify_telegram_auth(
    fields: dict[str, str],
    provided_hash: str,
    bot_token: str | None = None,
    max_age: int = TELEGRAM_AUTH_MAX_AGE_SECONDS,
) -> None:
    token = bot_token if bot_token is not None else settings.telegram_bot_token
    if not token:
        raise OAuthError(
            TELEGRAM_NOT_CONFIGURED_CODE,
            TELEGRAM_NOT_CONFIGURED_MESSAGE,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if not provided_hash:
        raise OAuthError(
            TELEGRAM_BAD_SIGNATURE_CODE,
            TELEGRAM_BAD_SIGNATURE_MESSAGE,
            status.HTTP_401_UNAUTHORIZED,
        )

    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hashlib.sha256(token.encode("utf-8")).digest()
    expected = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, provided_hash.lower()):
        raise OAuthError(
            TELEGRAM_BAD_SIGNATURE_CODE,
            TELEGRAM_BAD_SIGNATURE_MESSAGE,
            status.HTTP_401_UNAUTHORIZED,
        )

    try:
        auth_date = int(fields.get("auth_date", ""))
    except (TypeError, ValueError):
        raise OAuthError(
            TELEGRAM_STALE_AUTH_CODE, TELEGRAM_STALE_AUTH_MESSAGE, status.HTTP_401_UNAUTHORIZED
        )

    age = time.time() - auth_date
    if age > max_age or age < -TELEGRAM_CLOCK_SKEW_SECONDS:
        raise OAuthError(
            TELEGRAM_STALE_AUTH_CODE, TELEGRAM_STALE_AUTH_MESSAGE, status.HTTP_401_UNAUTHORIZED
        )


async def consume_telegram_payload(
    provided_hash: str, max_age: int = TELEGRAM_AUTH_MAX_AGE_SECONDS
) -> None:
    key = f"{TELEGRAM_USED_PREFIX}{provided_hash.lower()}"
    try:
        redis = get_redis()
        stored = await redis.set(key, "1", nx=True, ex=max_age + TELEGRAM_CLOCK_SKEW_SECONDS)
    except REDIS_ERRORS as exc:
        logger.warning("telegram replay protection unavailable, redis is down: %s", exc)
        raise OAuthError(
            TELEGRAM_UNAVAILABLE_CODE,
            TELEGRAM_UNAVAILABLE_MESSAGE,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if not stored:
        raise OAuthError(
            TELEGRAM_REPLAYED_CODE, TELEGRAM_REPLAYED_MESSAGE, status.HTTP_401_UNAUTHORIZED
        )


async def create_telegram_nonce(user_id: int) -> str:
    nonce = secrets.token_urlsafe(24)
    try:
        redis = get_redis()
        await redis.set(
            f"{TELEGRAM_NONCE_PREFIX}{nonce}", str(user_id), ex=TELEGRAM_NONCE_TTL_SECONDS
        )
    except REDIS_ERRORS as exc:
        logger.warning("telegram nonce could not be stored, redis is down: %s", exc)
        raise OAuthError(
            TELEGRAM_UNAVAILABLE_CODE,
            TELEGRAM_UNAVAILABLE_MESSAGE,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return nonce


async def consume_telegram_nonce(nonce: str, user_id: int) -> None:
    try:
        redis = get_redis()
        raw = await redis.getdel(f"{TELEGRAM_NONCE_PREFIX}{nonce}")
    except REDIS_ERRORS as exc:
        logger.warning("telegram nonce could not be verified, redis is down: %s", exc)
        raise OAuthError(
            TELEGRAM_UNAVAILABLE_CODE,
            TELEGRAM_UNAVAILABLE_MESSAGE,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if raw is None:
        raise OAuthError(
            TELEGRAM_INVALID_NONCE_CODE,
            TELEGRAM_INVALID_NONCE_MESSAGE,
            status.HTTP_401_UNAUTHORIZED,
        )
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "ignore")
    if str(raw) != str(user_id):
        raise OAuthError(
            TELEGRAM_INVALID_NONCE_CODE,
            TELEGRAM_INVALID_NONCE_MESSAGE,
            status.HTTP_401_UNAUTHORIZED,
        )


async def link_telegram_identity(
    db: AsyncSession, user: User, fields: dict[str, str]
) -> UserIdentity:
    return await link_identity(
        db,
        user,
        TELEGRAM_PROVIDER,
        str(fields["id"]),
        telegram_display_name(fields),
        TELEGRAM_IDENTITY_TAKEN_CODE,
        TELEGRAM_IDENTITY_TAKEN_MESSAGE,
        TELEGRAM_ALREADY_LINKED_CODE,
        TELEGRAM_ALREADY_LINKED_MESSAGE,
    )


async def unlink_telegram_identity(db: AsyncSession, user: User) -> None:
    identity = await get_user_identity(db, user.id, TELEGRAM_PROVIDER)
    if identity is None:
        raise OAuthError(
            TELEGRAM_NOT_LINKED_CODE, TELEGRAM_NOT_LINKED_MESSAGE, status.HTTP_404_NOT_FOUND
        )
    await db.delete(identity)
    await db.flush()
