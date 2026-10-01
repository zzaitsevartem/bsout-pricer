import hashlib
import hmac
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.email_verification_service import require_verified_email
from src.modules.payment.model.payment import Payment
from src.modules.payment.schema.payment import (
    PaymentCreateRequest,
    PaymentResponse,
    PlanResponse,
    SubscriptionCancelResponse,
    WebhookAck,
    WebhookEvent,
)
from src.modules.payment.service.payment_service import (
    CANCELED,
    FAILED,
    PENDING,
    SUCCEEDED,
    PaymentService,
)
from src.modules.payment.service.plans import PLANS, price_for
from src.modules.shared import get_current_user
from src.modules.shared.deps import get_current_admin

router = APIRouter(prefix="/api/payment", tags=["payment"])

SIGNATURE_HEADER = "X-Payment-Signature"


def _webhook_secret() -> str | None:
    configured = getattr(settings, "yookassa_webhook_secret", None)
    if configured:
        return str(configured)
    return os.getenv("YOOKASSA_WEBHOOK_SECRET") or None


def _signature_is_valid(secret: str, raw_body: bytes, signature: str | None) -> bool:
    # TODO: заменить на настоящую проверку подписи ЮKassa (сертификат/алгоритм провайдера),
    # пока используется HMAC-SHA256 общего секрета. Без секрета вебхук отвечает 503.
    if not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip().lower())


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans():
    return [
        PlanResponse(
            plan=definition.plan,
            name_ru=definition.name_ru,
            price=definition.price,
            first_payment_price=price_for(definition.plan, first_payment=True),
            duration_days=definition.duration_days,
            tracked_products=definition.tracked_products,
            stores=definition.stores,
            fuzzy_search=definition.fuzzy_search,
            price_alerts=definition.price_alerts,
            export_reports=definition.export_reports,
            support_ru=definition.support_ru,
            featured=definition.featured,
            sort_order=definition.sort_order,
        )
        for definition in sorted(PLANS.values(), key=lambda item: item.sort_order)
    ]


@router.post(
    "/subscribe",
    dependencies=[Depends(require_verified_email)],
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe(
    body: PaymentCreateRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.plan == PlanEnum.trial:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пробный тариф бесплатный и не оплачивается через этот эндпоинт",
        )

    amount = await PaymentService.amount_for(db, current_user.id, body.plan)
    idempotence_key = PaymentService.build_idempotence_key(
        current_user.id, body.plan, body.idempotence_key
    )
    payment, created = await PaymentService.create_pending_payment(
        db,
        user_id=current_user.id,
        plan=body.plan,
        idempotence_key=idempotence_key,
        amount=amount,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return payment


@router.get("/history", response_model=list[PaymentResponse])
async def payment_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await PaymentService.list_payments(db, current_user.id)


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    payment = await db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status != PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Платёж уже обработан: status={payment.status}",
        )

    await PaymentService.mark_paid(db, payment)
    return payment


@router.post("/webhook", response_model=WebhookAck)
async def provider_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    secret = _webhook_secret()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Проверка подписи вебхука не настроена: задайте YOOKASSA_WEBHOOK_SECRET",
        )

    raw_body = await request.body()
    if not _signature_is_valid(secret, raw_body, request.headers.get(SIGNATURE_HEADER)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
        )

    try:
        payload = json.loads(raw_body or b"{}")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed webhook payload"
        ) from None
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed webhook payload"
        )

    event = WebhookEvent.model_validate(payload)
    obj = event.object or {}
    metadata = obj.get("metadata") or {}
    provider_payment_id = obj.get("id")
    idempotence_key = metadata.get("idempotence_key") or payload.get("idempotence_key")

    payment = await PaymentService.find_payment_by_reference(
        db,
        provider_payment_id=str(provider_payment_id) if provider_payment_id else None,
        idempotence_key=str(idempotence_key) if idempotence_key else None,
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    event_name = (event.event or obj.get("status") or "").lower()

    if event_name.endswith(SUCCEEDED):
        if payment.status == SUCCEEDED:
            return WebhookAck(
                detail="already applied", payment_id=payment.id, status=payment.status
            )
        await PaymentService.mark_paid(
            db,
            payment,
            provider_payment_id=str(provider_payment_id) if provider_payment_id else None,
            raw=payload,
        )
        return WebhookAck(detail="applied", payment_id=payment.id, status=payment.status)

    if event_name.endswith((CANCELED, FAILED)):
        if payment.status != PENDING:
            return WebhookAck(
                detail="already applied", payment_id=payment.id, status=payment.status
            )
        new_status = FAILED if event_name.endswith(FAILED) else CANCELED
        await PaymentService.mark_status(db, payment, new_status, raw=payload)
        return WebhookAck(detail="applied", payment_id=payment.id, status=payment.status)

    return WebhookAck(detail="ignored", payment_id=payment.id, status=payment.status)


@router.post("/cancel", response_model=SubscriptionCancelResponse)
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == current_user.id,
            Subscription.is_active.is_(True),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")

    await PaymentService.cancel_subscription(db, subscription)

    return SubscriptionCancelResponse(
        detail="Автопродление отключено, доступ сохраняется до конца оплаченного периода",
        subscription_id=subscription.id,
        plan=subscription.plan,
        is_active=subscription.is_active,
        auto_renew=subscription.auto_renew,
        end_date=subscription.end_date,
        access_until=subscription.end_date,
    )
