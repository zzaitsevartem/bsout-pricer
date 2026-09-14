from decimal import Decimal

import pytest

from src.modules.auth.model.user import PlanEnum
from src.modules.payment.service.payment_service import PaymentService

pytestmark = pytest.mark.unit


def test_every_plan_has_a_price():
    assert set(PaymentService.PLAN_PRICES) == set(PlanEnum)


def test_trial_is_free_paid_plans_are_not():
    assert PaymentService.PLAN_PRICES[PlanEnum.trial] == Decimal("0")
    assert PaymentService.PLAN_PRICES[PlanEnum.basic] == Decimal("399")
    assert PaymentService.PLAN_PRICES[PlanEnum.advanced] == Decimal("499")
