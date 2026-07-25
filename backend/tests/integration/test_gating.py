from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from src.middleware.subscription_guard import (
    get_current_plan,
    has_feature,
    is_fuzzy_enabled,
    plans_with_feature,
    require_feature,
    tracked_products_limit_for,
)
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_access_token, hash_password

pytestmark = pytest.mark.integration

GATED_PATHS = (
    "/api/products",
    "/api/products/catalog",
    "/api/products/catalog/1",
    "/api/products/catalog/1/price-history",
    "/api/products/1",
    "/api/products/1/price-history",
)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(db, email: str) -> tuple[User, str]:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Gating User",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user, create_access_token(user.id)


async def _add_subscription(
    db,
    user_id: int,
    *,
    plan: PlanEnum = PlanEnum.trial,
    starts_days_ago: int = 0,
    ends_in_days: int = 7,
    is_active: bool = True,
) -> Subscription:
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user_id,
        plan=plan,
        start_date=now - timedelta(days=starts_days_ago),
        end_date=now + timedelta(days=ends_in_days),
        is_active=is_active,
    )
    db.add(subscription)
    await db.flush()
    return subscription


@pytest.mark.parametrize("path", GATED_PATHS)
async def test_product_endpoints_forbidden_without_subscription(client, db_session, path):
    slug = path.strip("/").replace("/", "-")
    _, token = await _make_user(db_session, f"nosub-{slug}@example.com")

    resp = await client.get(path, headers=_auth(token))

    assert resp.status_code == 403, f"{path} -> {resp.status_code} {resp.text}"
    detail = resp.json()["detail"]
    assert detail["code"] == "subscription_required"
    assert detail["message"].strip()


async def test_gated_403_is_distinguishable_from_unauthenticated_403(client, db_session):
    _, token = await _make_user(db_session, "distinguish@example.com")

    anonymous = await client.get("/api/products")
    gated = await client.get("/api/products", headers=_auth(token))

    assert anonymous.status_code == 403
    assert anonymous.json()["detail"] == "Not authenticated"
    assert gated.status_code == 403
    assert gated.json()["detail"]["code"] == "subscription_required"


@pytest.mark.parametrize("plan", [PlanEnum.trial, PlanEnum.basic, PlanEnum.advanced])
async def test_product_search_allowed_with_active_subscription(client, db_session, plan):
    user, token = await _make_user(db_session, f"active-{plan.value}@example.com")
    await _add_subscription(db_session, user.id, plan=plan)

    resp = await client.get("/api/products", headers=_auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 0


async def test_catalog_allowed_with_active_trial(client, db_session):
    user, token = await _make_user(db_session, "trialcatalog@example.com")
    await _add_subscription(db_session, user.id, plan=PlanEnum.trial)

    resp = await client.get("/api/products/catalog", headers=_auth(token))

    assert resp.status_code == 200, resp.text


async def test_expired_subscription_is_forbidden(client, db_session):
    user, token = await _make_user(db_session, "expired@example.com")
    await _add_subscription(db_session, user.id, starts_days_ago=40, ends_in_days=-1)

    resp = await client.get("/api/products", headers=_auth(token))

    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"]["code"] == "subscription_required"


async def test_deactivated_subscription_is_forbidden(client, db_session):
    user, token = await _make_user(db_session, "cancelled@example.com")
    await _add_subscription(db_session, user.id, plan=PlanEnum.advanced, is_active=False)

    resp = await client.get("/api/products", headers=_auth(token))

    assert resp.status_code == 403, resp.text


async def test_public_endpoints_stay_open_without_subscription(client, db_session):
    _, token = await _make_user(db_session, "public@example.com")

    assert (await client.get("/api/health")).status_code == 200
    assert (await client.get("/api/stores")).status_code == 200
    assert (await client.get("/api/categories")).status_code == 200
    assert (await client.get("/api/users/me", headers=_auth(token))).status_code == 200
    assert (await client.get("/api/search/history", headers=_auth(token))).status_code == 200


async def test_get_current_plan_reflects_active_subscription(db_session):
    user, _ = await _make_user(db_session, "currentplan@example.com")

    assert await get_current_plan(db_session, user.id) is None

    await _add_subscription(db_session, user.id, plan=PlanEnum.basic, ends_in_days=30)

    assert await get_current_plan(db_session, user.id) == PlanEnum.basic


async def test_fuzzy_enabled_only_on_advanced(db_session):
    trial_user, _ = await _make_user(db_session, "fuzzy-trial@example.com")
    basic_user, _ = await _make_user(db_session, "fuzzy-basic@example.com")
    advanced_user, _ = await _make_user(db_session, "fuzzy-advanced@example.com")
    nosub_user, _ = await _make_user(db_session, "fuzzy-nosub@example.com")

    await _add_subscription(db_session, trial_user.id, plan=PlanEnum.trial)
    await _add_subscription(db_session, basic_user.id, plan=PlanEnum.basic, ends_in_days=30)
    await _add_subscription(db_session, advanced_user.id, plan=PlanEnum.advanced, ends_in_days=30)

    assert await is_fuzzy_enabled(db_session, trial_user.id) is False
    assert await is_fuzzy_enabled(db_session, basic_user.id) is False
    assert await is_fuzzy_enabled(db_session, advanced_user.id) is True
    assert await is_fuzzy_enabled(db_session, nosub_user.id) is False


async def test_expired_advanced_does_not_enable_fuzzy(db_session):
    user, _ = await _make_user(db_session, "fuzzy-expired@example.com")
    await _add_subscription(
        db_session, user.id, plan=PlanEnum.advanced, starts_days_ago=40, ends_in_days=-1
    )

    assert await is_fuzzy_enabled(db_session, user.id) is False


@pytest.mark.parametrize("feature", ["fuzzy_search", "price_alerts", "export_reports"])
async def test_paid_features_are_advanced_only(db_session, feature):
    basic_user, _ = await _make_user(db_session, f"feat-basic-{feature}@example.com")
    advanced_user, _ = await _make_user(db_session, f"feat-adv-{feature}@example.com")
    await _add_subscription(db_session, basic_user.id, plan=PlanEnum.basic, ends_in_days=30)
    await _add_subscription(db_session, advanced_user.id, plan=PlanEnum.advanced, ends_in_days=30)

    assert await has_feature(db_session, basic_user.id, feature) is False
    assert await has_feature(db_session, advanced_user.id, feature) is True
    assert plans_with_feature(feature) == ["advanced"]


async def test_require_feature_rejects_plan_without_feature(db_session):
    user, _ = await _make_user(db_session, "reqfeat-basic@example.com")
    await _add_subscription(db_session, user.id, plan=PlanEnum.basic, ends_in_days=30)
    dependency = require_feature("fuzzy_search")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(db=db_session, current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "feature_unavailable"
    assert exc_info.value.detail["feature"] == "fuzzy_search"
    assert exc_info.value.detail["requiredPlans"] == ["advanced"]


async def test_require_feature_allows_plan_with_feature(db_session):
    user, _ = await _make_user(db_session, "reqfeat-adv@example.com")
    subscription = await _add_subscription(
        db_session, user.id, plan=PlanEnum.advanced, ends_in_days=30
    )
    dependency = require_feature("export_reports")

    result = await dependency(db=db_session, current_user=user)

    assert result.id == subscription.id


async def test_require_feature_without_subscription_reports_subscription_required(db_session):
    user, _ = await _make_user(db_session, "reqfeat-nosub@example.com")
    dependency = require_feature("price_alerts")

    with pytest.raises(HTTPException) as exc_info:
        await dependency(db=db_session, current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "subscription_required"


def test_require_feature_rejects_unknown_feature():
    with pytest.raises(ValueError):
        require_feature("teleportation")


async def test_tracked_products_limit_matches_plan_matrix(db_session):
    nosub_user, _ = await _make_user(db_session, "limit-nosub@example.com")
    trial_user, _ = await _make_user(db_session, "limit-trial@example.com")
    basic_user, _ = await _make_user(db_session, "limit-basic@example.com")
    advanced_user, _ = await _make_user(db_session, "limit-advanced@example.com")

    await _add_subscription(db_session, trial_user.id, plan=PlanEnum.trial)
    await _add_subscription(db_session, basic_user.id, plan=PlanEnum.basic, ends_in_days=30)
    await _add_subscription(db_session, advanced_user.id, plan=PlanEnum.advanced, ends_in_days=30)

    assert await tracked_products_limit_for(db_session, nosub_user.id) == 0
    assert await tracked_products_limit_for(db_session, trial_user.id) == 10
    assert await tracked_products_limit_for(db_session, basic_user.id) == 100
    assert await tracked_products_limit_for(db_session, advanced_user.id) == 500
