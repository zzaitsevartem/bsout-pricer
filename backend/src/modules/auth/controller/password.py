import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.auth.controller.auth import _client_info
from src.modules.auth.model.user import User
from src.modules.auth.schema.auth import TokenResponse
from src.modules.auth.schema.password import (
    MessageResponse,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
)
from src.modules.auth.service.password_service import (
    RESET_REQUESTED_DETAIL,
    InvalidCurrentPasswordError,
    PasswordResetError,
    change_password,
    confirm_password_reset,
    request_password_reset,
)
from src.modules.auth.service.token_service import issue_token_pair
from src.modules.shared import get_current_user

logger = logging.getLogger(__name__)

password_router = APIRouter(prefix="/api/auth", tags=["auth"])

PASSWORD_RESET_DONE_DETAIL = "Пароль изменён. Все прежние сеансы завершены."


@password_router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def password_reset_request(
    body: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    _, ip_address = _client_info(request)
    try:
        await request_password_reset(db, body.email, requested_ip=ip_address)
    except Exception:
        logger.exception("password reset request failed")
    return MessageResponse(detail=RESET_REQUESTED_DETAIL)


@password_router.post("/password-reset/confirm", response_model=MessageResponse)
async def password_reset_confirm(
    body: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        await confirm_password_reset(db, body.token, body.new_password)
    except PasswordResetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail)

    return MessageResponse(detail=PASSWORD_RESET_DONE_DETAIL)


@password_router.post("/password/change", response_model=TokenResponse)
async def password_change(
    body: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await change_password(db, current_user, body.current_password, body.new_password)
    except InvalidCurrentPasswordError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail)

    user_agent, ip_address = _client_info(request)
    access_token, refresh_token = await issue_token_pair(
        db, current_user.id, user_agent=user_agent, ip_address=ip_address
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
