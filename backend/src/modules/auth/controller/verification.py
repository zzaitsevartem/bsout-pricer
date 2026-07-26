from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.modules.auth.model.user import User
from src.modules.auth.schema.verification import (
    EmailConfirmRequest,
    EmailConfirmResponse,
    EmailResendResponse,
)
from src.modules.auth.service.email_verification_service import (
    ALREADY_VERIFIED_CODE,
    ALREADY_VERIFIED_MESSAGE,
    RATE_LIMITED_CODE,
    RATE_LIMITED_MESSAGE,
    RESEND_WINDOW_SECONDS,
    EmailVerificationError,
    VerificationMailer,
    confirm_email,
    consume_resend_quota,
    get_verification_mailer,
    issue_email_verification,
)
from src.modules.shared import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _request_ip(request: Request) -> str | None:
    if settings.rate_limit_trust_forwarded_for:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            first = forwarded.split(",")[0].strip()
            if first:
                return first[:64]
    if request.client is not None:
        return request.client.host[:64]
    return None


@router.post("/email/confirm", response_model=EmailConfirmResponse)
async def confirm_email_address(body: EmailConfirmRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await confirm_email(db, body.token)
    except EmailVerificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.as_detail())
    return EmailConfirmResponse(email_verified=True, email_verified_at=user.email_verified_at)


@router.post("/email/resend", response_model=EmailResendResponse)
async def resend_verification_email(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mailer: VerificationMailer = Depends(get_verification_mailer),
):
    if current_user.email_verified_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": ALREADY_VERIFIED_CODE, "message": ALREADY_VERIFIED_MESSAGE},
        )

    if not await consume_resend_quota(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": RATE_LIMITED_CODE, "message": RATE_LIMITED_MESSAGE},
            headers={"Retry-After": str(RESEND_WINDOW_SECONDS)},
        )

    try:
        token = await issue_email_verification(
            db,
            current_user,
            mailer=mailer,
            requested_ip=_request_ip(request),
            suppress_send_errors=False,
        )
    except EmailVerificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.as_detail())

    return EmailResendResponse(sent=True, expires_at=token.expires_at)
