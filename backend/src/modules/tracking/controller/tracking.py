from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.middleware.subscription_guard import (
    get_current_plan,
    require_active_subscription,
    tracked_products_limit_for,
)
from src.modules.auth.model.user import Subscription, User
from src.modules.payment.service.plans import get_plan
from src.modules.shared import get_current_user
from src.modules.tracking.schema.tracking import (
    TRACKING_LIMIT_REACHED_CODE,
    TrackedProductCreateRequest,
    TrackedProductListResponse,
    TrackedProductResponse,
    TrackedProductUpdateRequest,
    TrackingUsageResponse,
)
from src.modules.tracking.service.tracking_service import TrackingService

router = APIRouter(
    prefix="/api/tracking",
    tags=["tracking"],
    dependencies=[Depends(require_active_subscription)],
)

PRODUCT_NOT_FOUND = "Canonical product not found"
TRACKED_NOT_FOUND = "Tracked product not found"


def _limit_reached_detail(plan, limit: int, used: int) -> dict:
    name_ru = get_plan(plan).name_ru if plan is not None else "—"
    return {
        "code": TRACKING_LIMIT_REACHED_CODE,
        "limit": limit,
        "used": used,
        "plan": plan.value if plan is not None else None,
        "message": (
            f"Достигнут лимит тарифа «{name_ru}»: отслеживается {used} из {limit} товаров. "
            f"Перейдите на более высокий тариф, чтобы отслеживать больше позиций."
        ),
    }


@router.get("/usage", response_model=TrackingUsageResponse)
async def get_tracking_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    subscription: Subscription = Depends(require_active_subscription),
):
    used = await TrackingService.count_active(db, current_user.id)
    limit = await tracked_products_limit_for(db, current_user.id)
    return TrackingUsageResponse(
        used=used,
        limit=limit,
        remaining=max(limit - used, 0),
        plan=subscription.plan,
    )


@router.get("", response_model=TrackedProductListResponse)
async def list_tracked_products(
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results, total = await TrackingService.list_for_user(
        db=db,
        user_id=current_user.id,
        is_active=is_active,
        page=page,
        per_page=per_page,
    )
    return TrackedProductListResponse(results=results, total=total, page=page, per_page=per_page)


@router.post("", response_model=TrackedProductResponse, status_code=status.HTTP_201_CREATED)
async def create_tracked_product(
    payload: TrackedProductCreateRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    subscription: Subscription = Depends(require_active_subscription),
):
    snapshot = await TrackingService.product_snapshot(db, payload.product_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PRODUCT_NOT_FOUND)

    existing = await TrackingService.get_by_product(db, current_user.id, payload.product_id)
    if existing is not None and existing.is_active:
        if payload.target_price is not None:
            existing.target_price = payload.target_price
            await db.flush()
        response.status_code = status.HTTP_200_OK
        return await TrackingService.build_response(db, existing, snapshot)

    used = await TrackingService.count_active(db, current_user.id)
    limit = await tracked_products_limit_for(db, current_user.id)
    if used >= limit:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=_limit_reached_detail(subscription.plan, limit, used),
        )

    if existing is not None:
        tracked = await TrackingService.reactivate(
            db, existing, payload.target_price, snapshot["min_price_retail"]
        )
        response.status_code = status.HTTP_200_OK
    else:
        tracked = await TrackingService.create(
            db,
            user_id=current_user.id,
            product_id=payload.product_id,
            target_price=payload.target_price,
            last_seen_price=snapshot["min_price_retail"],
        )

    return await TrackingService.build_response(db, tracked, snapshot)


@router.patch("/{tracked_id}", response_model=TrackedProductResponse)
async def update_tracked_product(
    tracked_id: int,
    payload: TrackedProductUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tracked = await TrackingService.get_by_id(db, current_user.id, tracked_id)
    if tracked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TRACKED_NOT_FOUND)

    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_active") is True and not tracked.is_active:
        used = await TrackingService.count_active(db, current_user.id)
        limit = await tracked_products_limit_for(db, current_user.id)
        if used >= limit:
            plan = await get_current_plan(db, current_user.id)
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=_limit_reached_detail(plan, limit, used),
            )

    tracked = await TrackingService.apply_update(db, tracked, changes)
    return await TrackingService.build_response(db, tracked)


@router.delete("/{tracked_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tracked_product(
    tracked_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tracked = await TrackingService.get_by_id(db, current_user.id, tracked_id)
    if tracked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TRACKED_NOT_FOUND)

    await TrackingService.delete(db, tracked)
    return None
