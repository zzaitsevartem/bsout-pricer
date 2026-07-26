from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.modules.auth.model.user import User
from src.modules.auth.schema.oauth import (
    IdentityResponse,
    TelegramLinkRequest,
    VKAuthorizeResponse,
    VKAuthResponse,
    VKCallbackRequest,
)
from src.modules.auth.service.oauth_service import (
    VK_STATE_TTL_SECONDS,
    OAuthError,
    VKClient,
    build_vk_authorize_url,
    consume_vk_state,
    create_vk_state,
    ensure_vk_configured,
    get_vk_client,
    link_telegram_identity,
    link_vk_identity,
    login_or_register_vk,
    require_vk_state,
    unlink_telegram_identity,
    unlink_vk_identity,
    verify_telegram_auth,
)
from src.modules.auth.service.token_service import issue_token_pair
from src.modules.shared import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _http_error(exc: OAuthError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.as_detail())


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


@router.get("/vk/authorize", response_model=VKAuthorizeResponse)
async def vk_authorize():
    try:
        ensure_vk_configured()
        state = await create_vk_state()
    except OAuthError as exc:
        raise _http_error(exc)
    return VKAuthorizeResponse(
        authorize_url=build_vk_authorize_url(state),
        state=state,
        expires_in=VK_STATE_TTL_SECONDS,
    )


@router.post("/vk/callback", response_model=VKAuthResponse)
async def vk_callback(
    body: VKCallbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    vk_client: VKClient = Depends(get_vk_client),
):
    try:
        require_vk_state(await consume_vk_state(body.state))
        profile = await vk_client.exchange_code(body.code)
        user, created = await login_or_register_vk(db, profile)
    except OAuthError as exc:
        raise _http_error(exc)

    user_agent, ip_address = _client_info(request)
    access_token, refresh_token = await issue_token_pair(
        db, user.id, user_agent=user_agent, ip_address=ip_address
    )
    return VKAuthResponse(access_token=access_token, refresh_token=refresh_token, created=created)


@router.post("/vk/link", response_model=IdentityResponse)
async def vk_link(
    body: VKCallbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    vk_client: VKClient = Depends(get_vk_client),
):
    try:
        require_vk_state(await consume_vk_state(body.state))
        profile = await vk_client.exchange_code(body.code)
        identity = await link_vk_identity(db, current_user, profile)
    except OAuthError as exc:
        raise _http_error(exc)
    return IdentityResponse.model_validate(identity)


@router.delete("/vk/link", status_code=status.HTTP_204_NO_CONTENT)
async def vk_unlink(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await unlink_vk_identity(db, current_user)
    except OAuthError as exc:
        raise _http_error(exc)
    return None


@router.post("/telegram/link", response_model=IdentityResponse)
async def telegram_link(
    body: TelegramLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fields = body.signed_fields()
    try:
        verify_telegram_auth(fields, body.hash)
        identity = await link_telegram_identity(db, current_user, fields)
    except OAuthError as exc:
        raise _http_error(exc)
    return IdentityResponse.model_validate(identity)


@router.delete("/telegram/link", status_code=status.HTTP_204_NO_CONTENT)
async def telegram_unlink(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await unlink_telegram_identity(db, current_user)
    except OAuthError as exc:
        raise _http_error(exc)
    return None
