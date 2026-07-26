import logging
import time
from datetime import datetime, timezone
from uuid import uuid4

from redis.exceptions import RedisError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.service.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_by_id,
    refresh_token_expires_at,
)
from src.modules.cache.service.redis_cache import get_redis

logger = logging.getLogger(__name__)

ACCESS_DENYLIST_PREFIX = "auth:invalidate:"
REDIS_ERRORS = (RedisError, OSError)

REASON_LOGOUT = "logout"
REASON_ROTATED = "rotated"
REASON_REUSE = "reuse_detected"

INVALID_TOKEN_DETAIL = "Invalid or expired refresh token"
REVOKED_TOKEN_DETAIL = "Refresh token has been revoked"
REUSE_DETAIL = "Refresh token reuse detected, session revoked"
INACTIVE_USER_DETAIL = "User not found or inactive"

USER_AGENT_MAX = 255
IP_ADDRESS_MAX = 64


class TokenError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _clip(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:limit]


def access_token_ttl_seconds() -> int:
    return max(int(settings.access_token_expire_minutes) * 60, 1)


async def invalidate_access_tokens(user_id: int) -> bool:
    try:
        redis = get_redis()
        await redis.set(
            f"{ACCESS_DENYLIST_PREFIX}{user_id}",
            repr(time.time()),
            ex=access_token_ttl_seconds(),
        )
    except REDIS_ERRORS as exc:
        logger.warning(
            "access tokens for user %s were not added to the denylist, redis unavailable: %s",
            user_id,
            exc,
        )
        return False
    return True


async def access_tokens_invalid_before(user_id: int) -> float | None:
    try:
        redis = get_redis()
        raw = await redis.get(f"{ACCESS_DENYLIST_PREFIX}{user_id}")
    except REDIS_ERRORS as exc:
        logger.warning(
            "access token denylist not checked for user %s, redis unavailable: %s", user_id, exc
        )
        return None
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "ignore")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def access_token_issued_at(payload: dict) -> float | None:
    issued_at = payload.get("iat")
    if issued_at is None:
        expires_at = payload.get("exp")
        if expires_at is None:
            return None
        try:
            return float(expires_at) - access_token_ttl_seconds()
        except (TypeError, ValueError):
            return None
    try:
        return float(issued_at)
    except (TypeError, ValueError):
        return None


async def access_token_is_invalidated(payload: dict) -> bool:
    subject = payload.get("sub")
    if subject is None:
        return True
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        return True

    invalid_before = await access_tokens_invalid_before(user_id)
    if invalid_before is None:
        return False

    issued_at = access_token_issued_at(payload)
    if issued_at is None:
        return True
    return issued_at < invalid_before


async def get_token_by_jti(
    db: AsyncSession, jti: str, for_update: bool = False
) -> RefreshToken | None:
    query = select(RefreshToken).where(RefreshToken.jti == jti)
    if for_update:
        query = query.with_for_update()
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def issue_token_pair(
    db: AsyncSession,
    user_id: int,
    family_id: str | None = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str]:
    jti = uuid4().hex
    family = family_id or jti
    expires_at = refresh_token_expires_at()

    db.add(
        RefreshToken(
            jti=jti,
            family_id=family,
            user_id=user_id,
            expires_at=expires_at,
            user_agent=_clip(user_agent, USER_AGENT_MAX),
            ip_address=_clip(ip_address, IP_ADDRESS_MAX),
        )
    )
    await db.flush()

    refresh = create_refresh_token(user_id, jti=jti, family_id=family, expires_at=expires_at)
    return create_access_token(user_id), refresh


async def revoke_token(
    db: AsyncSession,
    token: RefreshToken,
    reason: str,
    replaced_by_jti: str | None = None,
) -> None:
    if token.revoked_at is None:
        token.revoked_at = _now()
        token.revoked_reason = reason
    if replaced_by_jti is not None:
        token.replaced_by_jti = replaced_by_jti
    await db.flush()


async def revoke_family(db: AsyncSession, family_id: str, reason: str) -> int:
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=_now(), revoked_reason=reason)
        .execution_options(synchronize_session=False)
    )
    await db.flush()
    return result.rowcount or 0


async def revoke_all_for_user(
    db: AsyncSession, user_id: int, reason: str, invalidate_access: bool = True
) -> int:
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=_now(), revoked_reason=reason)
        .execution_options(synchronize_session=False)
    )
    await db.flush()
    if invalidate_access:
        await invalidate_access_tokens(user_id)
    return result.rowcount or 0


def _decode_refresh(raw_token: str) -> dict:
    payload = decode_token(raw_token)
    if payload is None or payload.get("type") != "refresh":
        raise TokenError(INVALID_TOKEN_DETAIL)
    if not payload.get("jti") or not payload.get("sub"):
        raise TokenError(INVALID_TOKEN_DETAIL)
    return payload


async def _load_usable_token(db: AsyncSession, payload: dict) -> RefreshToken:
    stored = await get_token_by_jti(db, payload["jti"], for_update=True)
    if stored is None or str(stored.user_id) != str(payload["sub"]):
        raise TokenError(INVALID_TOKEN_DETAIL)
    if stored.replaced_by_jti is not None:
        await revoke_family(db, stored.family_id, REASON_REUSE)
        await db.commit()
        raise TokenError(REUSE_DETAIL)
    if stored.revoked_at is not None:
        raise TokenError(REVOKED_TOKEN_DETAIL)
    if _aware(stored.expires_at) <= _now():
        raise TokenError(INVALID_TOKEN_DETAIL)
    return stored


async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, str]:
    payload = _decode_refresh(raw_token)
    stored = await _load_usable_token(db, payload)

    user = await get_user_by_id(db, stored.user_id)
    if user is None or not user.is_active:
        raise TokenError(INACTIVE_USER_DETAIL)

    access, refresh = await issue_token_pair(
        db,
        stored.user_id,
        family_id=stored.family_id,
        user_agent=user_agent or stored.user_agent,
        ip_address=ip_address or stored.ip_address,
    )
    new_payload = decode_token(refresh)
    await revoke_token(db, stored, REASON_ROTATED, replaced_by_jti=new_payload["jti"])
    return access, refresh


async def revoke_session(db: AsyncSession, user_id: int, raw_token: str | None) -> int:
    if raw_token:
        payload = decode_token(raw_token)
        jti = payload.get("jti") if payload and payload.get("type") == "refresh" else None
        if jti:
            stored = await get_token_by_jti(db, jti)
            if stored is not None and stored.user_id == user_id:
                return await revoke_family(db, stored.family_id, REASON_LOGOUT)
    return await revoke_all_for_user(db, user_id, REASON_LOGOUT, invalidate_access=False)
