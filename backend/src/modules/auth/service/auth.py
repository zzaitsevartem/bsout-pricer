import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.modules.auth.model.user import PlanEnum, Subscription, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_PASSWORD_BYTES = 72


def password_byte_length(password: str) -> int:
    return len(password.encode("utf-8"))


def password_exceeds_bcrypt_limit(password: str) -> bool:
    return password_byte_length(password) > MAX_PASSWORD_BYTES


def hash_password(password: str) -> str:
    if password_exceeds_bcrypt_limit(password):
        raise ValueError(f"password must not exceed {MAX_PASSWORD_BYTES} bytes in utf-8")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    issued_at = time.time()
    expire = datetime.fromtimestamp(issued_at, tz=timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire, "iat": issued_at, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def refresh_token_expires_at(issued_at: datetime | None = None) -> datetime:
    base = issued_at or datetime.now(timezone.utc)
    return base + timedelta(days=settings.refresh_token_expire_days)


def create_refresh_token(
    user_id: int,
    jti: str | None = None,
    family_id: str | None = None,
    expires_at: datetime | None = None,
) -> str:
    token_jti = jti or uuid4().hex
    expire = expires_at or refresh_token_expires_at()
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": token_jti,
        "family_id": family_id or token_jti,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require_exp": True, "verify_exp": True},
        )
    except JWTError:
        return None
    if payload.get("exp") is None:
        return None
    return payload


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_identifier(db: AsyncSession, identifier: str) -> User | None:
    user = await get_user_by_username(db, identifier)
    if user is not None:
        return user
    return await get_user_by_email(db, identifier)


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str,
    phone: str | None,
    company: str | None,
    username: str | None = None,
) -> User:
    user = User(
        email=email,
        username=username,
        username_changed_at=datetime.now(timezone.utc) if username is not None else None,
        password_hash=hash_password(password),
        full_name=full_name,
        phone=phone,
        company=company,
    )
    db.add(user)
    await db.flush()
    return user


async def has_active_subscription(db: AsyncSession, user_id: int) -> bool:
    result = await db.execute(
        select(Subscription.id)
        .where(
            Subscription.user_id == user_id,
            Subscription.is_active.is_(True),
            Subscription.end_date > func.now(),
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def grant_trial_subscription(db: AsyncSession, user: User) -> Subscription | None:
    if user.trial_used:
        return None
    if await has_active_subscription(db, user.id):
        return None

    from src.modules.payment.service.plans import get_plan

    definition = get_plan(PlanEnum.trial)
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user.id,
        plan=PlanEnum.trial,
        start_date=now,
        end_date=now + timedelta(days=definition.duration_days),
        is_active=True,
        auto_renew=False,
    )
    user.trial_used = True
    db.add(subscription)
    await db.flush()
    return subscription


DUMMY_PASSWORD_HASH = hash_password("bscout-timing-equaliser")


async def authenticate_user(db: AsyncSession, identifier: str, password: str) -> User | None:
    user = await get_user_by_identifier(db, identifier)
    if user is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user
