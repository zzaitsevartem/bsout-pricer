from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.payment.service.plans import PLANS, get_plan, tracked_products_limit
from src.modules.shared import get_current_user

SUBSCRIPTION_REQUIRED_CODE = "subscription_required"
FEATURE_UNAVAILABLE_CODE = "feature_unavailable"

SUBSCRIPTION_REQUIRED_MESSAGE = (
    "Требуется активная подписка. Оформите тариф, чтобы пользоваться поиском и сравнением цен."
)

GATED_FEATURES: dict[str, str] = {
    "fuzzy_search": "Нечёткий поиск",
    "price_alerts": "Оповещения о снижении цены",
    "export_reports": "Экспорт отчётов",
}


def plans_with_feature(feature: str) -> list[str]:
    return [plan.value for plan, definition in PLANS.items() if getattr(definition, feature)]


def subscription_required_detail() -> dict:
    return {
        "code": SUBSCRIPTION_REQUIRED_CODE,
        "message": SUBSCRIPTION_REQUIRED_MESSAGE,
    }


def feature_unavailable_detail(feature: str) -> dict:
    required = plans_with_feature(feature)
    names = ", ".join(PLANS[PlanEnum(plan)].name_ru for plan in required)
    return {
        "code": FEATURE_UNAVAILABLE_CODE,
        "feature": feature,
        "requiredPlans": required,
        "message": f"«{GATED_FEATURES[feature]}» доступен на тарифах: {names}.",
    }


async def get_active_subscription(db: AsyncSession, user_id: int) -> Subscription | None:
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.is_active.is_(True),
            Subscription.end_date > func.now(),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def require_active_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Subscription:
    subscription = await get_active_subscription(db, current_user.id)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=subscription_required_detail(),
        )
    return subscription


async def get_current_plan(db: AsyncSession, user_id: int) -> PlanEnum | None:
    subscription = await get_active_subscription(db, user_id)
    if subscription is None:
        return None
    return subscription.plan


async def has_feature(db: AsyncSession, user_id: int, feature: str) -> bool:
    plan = await get_current_plan(db, user_id)
    if plan is None:
        return False
    return bool(getattr(get_plan(plan), feature))


def require_feature(feature: str) -> Callable[..., Awaitable[Subscription]]:
    if feature not in GATED_FEATURES:
        raise ValueError(f"unknown gated feature: {feature}")

    async def dependency(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Subscription:
        subscription = await get_active_subscription(db, current_user.id)
        if subscription is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=subscription_required_detail(),
            )
        if not getattr(get_plan(subscription.plan), feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=feature_unavailable_detail(feature),
            )
        return subscription

    return dependency


async def tracked_products_limit_for(db: AsyncSession, user_id: int) -> int:
    plan = await get_current_plan(db, user_id)
    if plan is None:
        return 0
    return tracked_products_limit(plan)


async def is_fuzzy_enabled(db: AsyncSession, user_id: int) -> bool:
    return await has_feature(db, user_id, "fuzzy_search")
