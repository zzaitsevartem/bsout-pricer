from dataclasses import dataclass
from decimal import Decimal

from src.modules.auth.model.user import PlanEnum


@dataclass(frozen=True)
class PlanDefinition:
    plan: PlanEnum
    name_ru: str
    price: Decimal
    duration_days: int
    tracked_products: int
    stores: int
    fuzzy_search: bool
    price_alerts: bool
    export_reports: bool
    support_ru: str


PLANS: dict[PlanEnum, PlanDefinition] = {
    PlanEnum.trial: PlanDefinition(
        plan=PlanEnum.trial,
        name_ru="Пробный",
        price=Decimal("0"),
        duration_days=7,
        tracked_products=10,
        stores=5,
        fuzzy_search=False,
        price_alerts=False,
        export_reports=False,
        support_ru="—",
    ),
    PlanEnum.basic: PlanDefinition(
        plan=PlanEnum.basic,
        name_ru="Базовый",
        price=Decimal("399"),
        duration_days=30,
        tracked_products=100,
        stores=5,
        fuzzy_search=False,
        price_alerts=False,
        export_reports=False,
        support_ru="Рабочие часы",
    ),
    PlanEnum.advanced: PlanDefinition(
        plan=PlanEnum.advanced,
        name_ru="Продвинутый",
        price=Decimal("499"),
        duration_days=30,
        tracked_products=500,
        stores=5,
        fuzzy_search=True,
        price_alerts=True,
        export_reports=True,
        support_ru="24/7",
    ),
}

FIRST_PAYMENT_DISCOUNT = Decimal("0.20")


def get_plan(plan: PlanEnum) -> PlanDefinition:
    return PLANS[plan]


def price_for(plan: PlanEnum, first_payment: bool = False) -> Decimal:
    base = PLANS[plan].price
    if first_payment and base > 0:
        return (base * (Decimal("1") - FIRST_PAYMENT_DISCOUNT)).quantize(Decimal("0.01"))
    return base


def tracked_products_limit(plan: PlanEnum) -> int:
    return PLANS[plan].tracked_products
