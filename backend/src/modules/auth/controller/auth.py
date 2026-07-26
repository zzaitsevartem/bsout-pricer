import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.modules.auth.model.user import User
from src.modules.auth.schema.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from src.modules.auth.service.auth import (
    authenticate_user,
    create_user,
    get_user_by_email,
    grant_trial_subscription,
)
from src.modules.auth.service.email_verification_service import issue_email_verification
from src.modules.auth.service.token_service import (
    TokenError,
    issue_token_pair,
    revoke_session,
    rotate_refresh_token,
)
from src.modules.shared import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

REGISTRATION_REJECTED_DETAIL = "Registration could not be completed"
INVALID_CREDENTIALS_DETAIL = "Invalid email or password"


def _client_info(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip_address = None
    if settings.rate_limit_trust_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
    if ip_address is None and request.client is not None:
        ip_address = request.client.host
    return user_agent, ip_address


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=REGISTRATION_REJECTED_DETAIL
        )

    try:
        async with db.begin_nested():
            user = await create_user(
                db=db,
                email=body.email,
                password=body.password,
                full_name=body.full_name,
                phone=body.phone,
                company=body.company,
            )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=REGISTRATION_REJECTED_DETAIL
        )

    try:
        async with db.begin_nested():
            await grant_trial_subscription(db, user)
    except Exception:
        logger.exception("failed to grant trial subscription for user %s", user.id)

    user_agent, ip_address = _client_info(request)

    try:
        await issue_email_verification(db, user, requested_ip=ip_address)
    except Exception:
        logger.exception("failed to send verification email for user %s", user.id)

    access_token, refresh_token = await issue_token_pair(
        db, user.id, user_agent=user_agent, ip_address=ip_address
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS_DETAIL
        )

    user_agent, ip_address = _client_info(request)
    access_token, refresh_token = await issue_token_pair(
        db, user.id, user_agent=user_agent, ip_address=ip_address
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user_agent, ip_address = _client_info(request)
    try:
        access_token, refresh_token = await rotate_refresh_token(
            db, body.refresh_token, user_agent=user_agent, ip_address=ip_address
        )
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.detail)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await revoke_session(db, current_user.id, body.refresh_token if body else None)
    return None
