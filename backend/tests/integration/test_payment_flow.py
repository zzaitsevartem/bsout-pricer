from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select

from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import create_access_token
from src.modules.payment.model.payment import Payment
from src.modules.payment.service import yookassa as yookassa_module
from src.modules.payment.service.payment_service import PaymentService

pytestmark = pytest.mark.integration

PROVIDER_SHOP_ID = "test-shop"
PROVIDER_SECRET_KEY = "test-secret"


def _provider_env(monkeypatch):
    monkeypatch.setenv("YOOKASSA_SHOP_ID", PROVIDER_SHOP_ID)
    monkeypatch.setenv("YOOKASSA_SECRET_KEY", PROVIDER_SECRET_KEY)


def _remote_object(status: str, paid: bool, value: str = "319.20") -> dict:
    return {
        "id": "yk-test-1",
        "status": status,
        "paid": paid,
        "amount": {"value": value, "currency": "RUB"},
    }


def _provider_api(monkeypatch, objects: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                200,
                json={
                    "id": "yk-test-1",
                    "confirmation": {"confirmation_url": "https://pay.example/x"},
                },
            )
        payment_id = request.url.path.rsplit("/", 1)[-1]
        if payment_id in objects:
            return httpx.Response(200, json=objects[payment_id])
        return httpx.Response(404, json={})

    monkeypatch.setattr(
        yookassa_module,
        "_client_factory",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def _make_user(
    db, email: str, *, is_admin: bool = False, email_verified: bool = True
) -> User:
    user = User(
        email=email,
        password_hash="x",
        full_name="Pay User",
        is_active=True,
        is_admin=is_admin,
        email_verified_at=datetime.now(timezone.utc) if email_verified else None,
    )
    db.add(user)
    await db.flush()
    return user


async def _count_subscriptions(db, user_id: int, *, only_active: bool = False) -> int:
    query = select(func.count()).select_from(Subscription).where(Subscription.user_id == user_id)
    if only_active:
        query = query.where(Subscription.is_active.is_(True))
    return (await db.execute(query)).scalar() or 0


async def _count_payments(db, user_id: int) -> int:
    return (
        await db.execute(
            select(func.count()).select_from(Payment).where(Payment.user_id == user_id)
        )
    ).scalar() or 0


async def _get_payment(db, payment_id: int) -> Payment:
    return (await db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one()


async def _subscribe_basic(client, user: User) -> dict:
    resp = await client.post("/api/payment/subscribe", json={"plan": "basic"}, headers=_auth(user))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_plans_endpoint_is_public(client):
    resp = await client.get("/api/payment/plans")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert {item["plan"] for item in body} == {"trial", "basic", "advanced"}


async def test_plans_expose_prices_limits_and_features(client):
    body = (await client.get("/api/payment/plans")).json()
    by_plan = {item["plan"]: item for item in body}

    assert Decimal(by_plan["basic"]["price"]) == Decimal("399")
    assert Decimal(by_plan["basic"]["first_payment_price"]) == Decimal("319.20")
    assert Decimal(by_plan["advanced"]["price"]) == Decimal("499")
    assert Decimal(by_plan["advanced"]["first_payment_price"]) == Decimal("399.20")
    assert Decimal(by_plan["trial"]["price"]) == Decimal("0")
    assert Decimal(by_plan["trial"]["first_payment_price"]) == Decimal("0")

    assert by_plan["basic"]["tracked_products"] == 100
    assert by_plan["advanced"]["tracked_products"] == 500
    assert by_plan["advanced"]["fuzzy_search"] is True
    assert by_plan["advanced"]["price_alerts"] is True
    assert by_plan["advanced"]["export_reports"] is True
    assert by_plan["basic"]["fuzzy_search"] is False
    assert by_plan["basic"]["stores"] == by_plan["advanced"]["stores"] == 5


async def test_subscribe_requires_authentication(client):
    resp = await client.post("/api/payment/subscribe", json={"plan": "basic"})

    assert resp.status_code == 403


async def test_subscribe_creates_pending_payment_without_subscription(client, db_session):
    user = await _make_user(db_session, "pending@example.com")

    resp = await client.post("/api/payment/subscribe", json={"plan": "basic"}, headers=_auth(user))

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["plan"] == "basic"
    assert body["user_id"] == user.id
    assert body["subscription_id"] is None
    assert body["provider"] == "manual"
    assert "confirmation_url" in body
    assert await _count_subscriptions(db_session, user.id) == 0


async def test_subscribe_applies_first_payment_discount(client, db_session):
    user = await _make_user(db_session, "discount@example.com")

    resp = await client.post(
        "/api/payment/subscribe", json={"plan": "advanced"}, headers=_auth(user)
    )

    assert Decimal(resp.json()["amount"]) == Decimal("399.20")


async def test_second_payment_is_full_price_after_first_succeeds(client, db_session):
    user = await _make_user(db_session, "second@example.com")
    admin = await _make_user(db_session, "admin-second@example.com", is_admin=True)

    first = await client.post(
        "/api/payment/subscribe",
        json={"plan": "basic", "idempotence_key": "first"},
        headers=_auth(user),
    )
    assert Decimal(first.json()["amount"]) == Decimal("319.20")

    confirmed = await client.post(
        f"/api/payment/{first.json()['id']}/confirm", headers=_auth(admin)
    )
    assert confirmed.status_code == 200, confirmed.text

    second = await client.post(
        "/api/payment/subscribe",
        json={"plan": "basic", "idempotence_key": "second"},
        headers=_auth(user),
    )

    assert second.status_code == 201, second.text
    assert Decimal(second.json()["amount"]) == Decimal("399.00")


async def test_subscribe_is_idempotent_for_repeated_clicks(client, db_session):
    user = await _make_user(db_session, "doubleclick@example.com")

    first = await client.post("/api/payment/subscribe", json={"plan": "basic"}, headers=_auth(user))
    second = await client.post(
        "/api/payment/subscribe", json={"plan": "basic"}, headers=_auth(user)
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]
    assert await _count_payments(db_session, user.id) == 1


async def test_subscribe_is_idempotent_with_explicit_key(client, db_session):
    user = await _make_user(db_session, "explicitkey@example.com")
    payload = {"plan": "advanced", "idempotence_key": "checkout-42"}

    first = await client.post("/api/payment/subscribe", json=payload, headers=_auth(user))
    second = await client.post("/api/payment/subscribe", json=payload, headers=_auth(user))

    assert first.json()["id"] == second.json()["id"]
    assert await _count_payments(db_session, user.id) == 1


async def test_idempotence_key_is_scoped_per_user(client, db_session):
    first_user = await _make_user(db_session, "scope-a@example.com")
    second_user = await _make_user(db_session, "scope-b@example.com")
    payload = {"plan": "basic", "idempotence_key": "shared-key"}

    first = await client.post("/api/payment/subscribe", json=payload, headers=_auth(first_user))
    second = await client.post("/api/payment/subscribe", json=payload, headers=_auth(second_user))

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] != second.json()["id"]
    assert second.json()["user_id"] == second_user.id


async def test_subscribe_rejects_trial_plan(client, db_session):
    user = await _make_user(db_session, "trial@example.com")

    resp = await client.post("/api/payment/subscribe", json={"plan": "trial"}, headers=_auth(user))

    assert resp.status_code == 400, resp.text
    assert "Пробный" in resp.json()["detail"]
    assert await _count_payments(db_session, user.id) == 0


async def test_confirm_requires_admin(client, db_session):
    user = await _make_user(db_session, "notadmin@example.com")
    payment_id = (
        await client.post("/api/payment/subscribe", json={"plan": "basic"}, headers=_auth(user))
    ).json()["id"]

    resp = await client.post(f"/api/payment/{payment_id}/confirm", headers=_auth(user))

    assert resp.status_code == 403
    assert await _count_subscriptions(db_session, user.id) == 0


async def test_confirm_unknown_payment_returns_404(client, db_session):
    admin = await _make_user(db_session, "admin-404@example.com", is_admin=True)

    resp = await client.post("/api/payment/9999999/confirm", headers=_auth(admin))

    assert resp.status_code == 404


async def test_confirm_activates_exactly_one_subscription(client, db_session):
    user = await _make_user(db_session, "confirm@example.com")
    admin = await _make_user(db_session, "admin-confirm@example.com", is_admin=True)
    payment_id = (
        await client.post("/api/payment/subscribe", json={"plan": "advanced"}, headers=_auth(user))
    ).json()["id"]

    resp = await client.post(f"/api/payment/{payment_id}/confirm", headers=_auth(admin))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "succeeded"
    assert body["paid_at"] is not None
    assert body["subscription_id"] is not None
    assert await _count_subscriptions(db_session, user.id, only_active=True) == 1

    subscription = (
        await db_session.execute(
            select(Subscription).where(Subscription.id == body["subscription_id"])
        )
    ).scalar_one()
    assert subscription.user_id == user.id
    assert subscription.plan == PlanEnum.advanced


async def test_second_confirm_returns_409_and_no_second_subscription(client, db_session):
    user = await _make_user(db_session, "double-confirm@example.com")
    admin = await _make_user(db_session, "admin-double@example.com", is_admin=True)
    payment_id = (
        await client.post("/api/payment/subscribe", json={"plan": "basic"}, headers=_auth(user))
    ).json()["id"]

    first = await client.post(f"/api/payment/{payment_id}/confirm", headers=_auth(admin))
    second = await client.post(f"/api/payment/{payment_id}/confirm", headers=_auth(admin))

    assert first.status_code == 200, first.text
    assert second.status_code == 409, second.text
    assert await _count_subscriptions(db_session, user.id) == 1


async def test_webhook_without_provider_credentials_returns_503(client, db_session, monkeypatch):
    monkeypatch.delenv("YOOKASSA_SHOP_ID", raising=False)
    monkeypatch.delenv("YOOKASSA_SECRET_KEY", raising=False)
    user = await _make_user(db_session, "webhook-nosecret@example.com")
    payment_id = (
        await client.post("/api/payment/subscribe", json={"plan": "basic"}, headers=_auth(user))
    ).json()["id"]

    resp = await client.post(
        "/api/payment/webhook",
        json={"event": "payment.succeeded", "object": {"id": "yk-1"}},
    )

    assert resp.status_code == 503, resp.text
    payment = await _get_payment(db_session, payment_id)
    assert payment.status == "pending"
    assert await _count_subscriptions(db_session, user.id) == 0


async def test_webhook_succeeded_activates_subscription_once(client, db_session, monkeypatch):
    _provider_env(monkeypatch)
    _provider_api(monkeypatch, {"yk-test-1": _remote_object("succeeded", True)})
    user = await _make_user(db_session, "webhook-ok@example.com")
    payment = await _subscribe_basic(client, user)

    first = await client.post("/api/payment/webhook", json={"object": {"id": "yk-test-1"}})
    second = await client.post("/api/payment/webhook", json={"object": {"id": "yk-test-1"}})

    assert first.status_code == 200, first.text
    assert first.json()["detail"] == "applied"
    assert second.status_code == 200, second.text
    assert second.json()["detail"] == "already applied"

    stored = await _get_payment(db_session, payment["id"])
    assert stored.status == "succeeded"
    assert stored.provider_payment_id == "yk-test-1"
    assert stored.subscription_id is not None
    assert await _count_subscriptions(db_session, user.id, only_active=True) == 1
    assert await _count_subscriptions(db_session, user.id) == 1


async def test_webhook_ignores_forged_body_when_provider_says_pending(
    client, db_session, monkeypatch
):
    _provider_env(monkeypatch)
    _provider_api(monkeypatch, {"yk-test-1": _remote_object("pending", False)})
    user = await _make_user(db_session, "webhook-forged@example.com")
    payment = await _subscribe_basic(client, user)

    resp = await client.post(
        "/api/payment/webhook",
        json={"event": "payment.succeeded", "object": {"id": "yk-test-1", "status": "succeeded"}},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["detail"] == "ignored"
    stored = await _get_payment(db_session, payment["id"])
    assert stored.status == "pending"
    assert await _count_subscriptions(db_session, user.id) == 0


async def test_webhook_canceled_sets_status_without_subscription(client, db_session, monkeypatch):
    _provider_env(monkeypatch)
    _provider_api(monkeypatch, {"yk-test-1": _remote_object("canceled", False)})
    user = await _make_user(db_session, "webhook-cancel@example.com")
    payment = await _subscribe_basic(client, user)

    resp = await client.post("/api/payment/webhook", json={"object": {"id": "yk-test-1"}})

    assert resp.status_code == 200, resp.text
    stored = await _get_payment(db_session, payment["id"])
    assert stored.status == "canceled"
    assert await _count_subscriptions(db_session, user.id) == 0


async def test_webhook_amount_mismatch_returns_409(client, db_session, monkeypatch):
    _provider_env(monkeypatch)
    _provider_api(monkeypatch, {"yk-test-1": _remote_object("succeeded", True, value="1.00")})
    user = await _make_user(db_session, "webhook-mismatch@example.com")
    payment = await _subscribe_basic(client, user)

    resp = await client.post("/api/payment/webhook", json={"object": {"id": "yk-test-1"}})

    assert resp.status_code == 409, resp.text
    stored = await _get_payment(db_session, payment["id"])
    assert stored.status == "pending"
    assert await _count_subscriptions(db_session, user.id) == 0


async def test_webhook_provider_unreachable_returns_502(client, db_session, monkeypatch):
    _provider_env(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                200,
                json={
                    "id": "yk-test-1",
                    "confirmation": {"confirmation_url": "https://pay.example/x"},
                },
            )
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(
        yookassa_module,
        "_client_factory",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    user = await _make_user(db_session, "webhook-down@example.com")
    payment = await _subscribe_basic(client, user)

    resp = await client.post("/api/payment/webhook", json={"object": {"id": "yk-test-1"}})

    assert resp.status_code == 502, resp.text
    stored = await _get_payment(db_session, payment["id"])
    assert stored.status == "pending"
    assert await _count_subscriptions(db_session, user.id) == 0


async def test_webhook_for_unknown_payment_returns_404(client, monkeypatch):
    _provider_env(monkeypatch)
    _provider_api(monkeypatch, {})

    resp = await client.post("/api/payment/webhook", json={"object": {"id": "yk-nope"}})

    assert resp.status_code == 404


async def test_history_returns_only_own_payments(client, db_session):
    user = await _make_user(db_session, "history@example.com")
    stranger = await _make_user(db_session, "history-other@example.com")

    await client.post(
        "/api/payment/subscribe",
        json={"plan": "basic", "idempotence_key": "h1"},
        headers=_auth(user),
    )
    await client.post(
        "/api/payment/subscribe",
        json={"plan": "advanced", "idempotence_key": "h2"},
        headers=_auth(user),
    )
    await client.post("/api/payment/subscribe", json={"plan": "basic"}, headers=_auth(stranger))

    resp = await client.get("/api/payment/history", headers=_auth(user))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 2
    assert {item["user_id"] for item in body} == {user.id}
    assert {item["plan"] for item in body} == {"basic", "advanced"}
    assert all(item["status"] == "pending" for item in body)


async def test_history_requires_authentication(client):
    assert (await client.get("/api/payment/history")).status_code == 403


async def test_cancel_keeps_access_until_end_date(client, db_session):
    user = await _make_user(db_session, "cancel@example.com")
    subscription = await PaymentService.create_subscription(db_session, user.id, PlanEnum.advanced)

    resp = await client.post("/api/payment/cancel", headers=_auth(user))

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["auto_renew"] is False
    assert body["is_active"] is True
    assert body["access_until"] == body["end_date"]

    await db_session.refresh(subscription)
    assert subscription.auto_renew is False
    assert subscription.is_active is True

    from src.middleware.subscription_guard import get_active_subscription

    still_active = await get_active_subscription(db_session, user.id)
    assert still_active is not None
    assert still_active.id == subscription.id


async def test_cancel_deactivates_already_expired_subscription(client, db_session):
    user = await _make_user(db_session, "cancel-expired@example.com")
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user.id,
        plan=PlanEnum.basic,
        start_date=now - timedelta(days=40),
        end_date=now - timedelta(days=10),
        is_active=True,
        auto_renew=True,
    )
    db_session.add(subscription)
    await db_session.flush()

    resp = await client.post("/api/payment/cancel", headers=_auth(user))

    assert resp.status_code == 200, resp.text
    assert resp.json()["is_active"] is False
    await db_session.refresh(subscription)
    assert subscription.is_active is False
    assert subscription.auto_renew is False


async def test_cancel_without_subscription_returns_404(client, db_session):
    user = await _make_user(db_session, "cancel-none@example.com")

    assert (await client.post("/api/payment/cancel", headers=_auth(user))).status_code == 404


async def test_subscribe_creates_provider_payment_when_configured(client, db_session, monkeypatch):
    monkeypatch.setenv("YOOKASSA_SHOP_ID", "shop-1")
    monkeypatch.setenv("YOOKASSA_SECRET_KEY", "secret-1")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "yk-int-1",
                "confirmation": {"confirmation_url": "https://pay.example/x"},
            },
        )

    monkeypatch.setattr(
        yookassa_module,
        "_client_factory",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    user = await _make_user(db_session, "provider@example.com")
    resp = await client.post("/api/payment/subscribe", json={"plan": "basic"}, headers=_auth(user))

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["provider"] == "yookassa"
    assert body["provider_payment_id"] == "yk-int-1"
    assert body["confirmation_url"] == "https://pay.example/x"
