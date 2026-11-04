from dataclasses import replace
from decimal import Decimal

import pytest

from src.modules.auth.model.user import PlanEnum
from src.modules.payment.service.payment_service import PaymentService
from src.modules.payment.service.plans import PLANS, price_for

pytestmark = pytest.mark.unit


def test_every_plan_has_a_price():
    assert set(PaymentService.PLAN_PRICES) == set(PlanEnum)


def test_trial_is_free_paid_plans_are_not():
    assert PaymentService.PLAN_PRICES[PlanEnum.trial] == Decimal("0")
    assert PaymentService.PLAN_PRICES[PlanEnum.basic] == Decimal("399")
    assert PaymentService.PLAN_PRICES[PlanEnum.advanced] == Decimal("499")


@pytest.mark.parametrize(
    ("plan", "expected"),
    [(PlanEnum.trial, "0"), (PlanEnum.basic, "319"), (PlanEnum.advanced, "399")],
)
def test_first_payment_prices_are_whole_rubles(plan, expected):
    assert price_for(plan, first_payment=True) == Decimal(expected)


def test_discount_rounds_half_ruble_up(monkeypatch):
    monkeypatch.setitem(
        PLANS, PlanEnum.basic, replace(PLANS[PlanEnum.basic], price=Decimal("401.875"))
    )
    assert price_for(PlanEnum.basic, first_payment=True) == Decimal("322")
