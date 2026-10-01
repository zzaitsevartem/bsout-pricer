import base64
import json
from decimal import Decimal

import httpx
import pytest

from src.modules.payment.service import yookassa

pytestmark = pytest.mark.unit

SHOP_ID = "12345"
SECRET_KEY = "test-secret-key"  # noqa: S105


def _authed_env(monkeypatch):
    monkeypatch.setenv("YOOKASSA_SHOP_ID", SHOP_ID)
    monkeypatch.setenv("YOOKASSA_SECRET_KEY", SECRET_KEY)


def _success_body():
    return {"id": "yk-abc-123", "confirmation": {"confirmation_url": "https://pay.example/1"}}


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_is_configured_false_without_credentials(monkeypatch):
    monkeypatch.delenv("YOOKASSA_SHOP_ID", raising=False)
    monkeypatch.delenv("YOOKASSA_SECRET_KEY", raising=False)
    assert yookassa.is_configured() is False


async def test_is_configured_true_with_env(monkeypatch):
    _authed_env(monkeypatch)
    assert yookassa.is_configured() is True


async def test_create_payment_returns_provider_id_and_link(monkeypatch):
    _authed_env(monkeypatch)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization")
        seen["idempotence_key"] = request.headers.get("idempotence-key")
        seen["payload"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json=_success_body())

    provider_id, confirmation_url = await yookassa.create_payment(
        amount=Decimal("319.20"),
        currency="RUB",
        description="test",
        return_url="https://app.example/subscription",
        idempotence_key="key-1",
        metadata={"payment_id": "7"},
        client=_client(handler),
    )

    assert provider_id == "yk-abc-123"
    assert confirmation_url == "https://pay.example/1"
    expected_auth = base64.b64encode(f"{SHOP_ID}:{SECRET_KEY}".encode()).decode()
    assert seen["authorization"] == f"Basic {expected_auth}"
    assert seen["idempotence_key"] == "key-1"
    assert seen["payload"]["amount"] == {"value": "319.20", "currency": "RUB"}
    assert seen["payload"]["capture"] is True
    assert seen["payload"]["confirmation"]["return_url"] == "https://app.example/subscription"


async def test_create_payment_rejects_provider_error(monkeypatch):
    _authed_env(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"type": "error"})

    with pytest.raises(yookassa.YooKassaError):
        await yookassa.create_payment(
            amount=Decimal("100"),
            currency="RUB",
            description="test",
            return_url="https://app.example/subscription",
            idempotence_key="key-2",
            metadata={},
            client=_client(handler),
        )


async def test_create_payment_rejects_invalid_json(monkeypatch):
    _authed_env(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    with pytest.raises(yookassa.YooKassaError):
        await yookassa.create_payment(
            amount=Decimal("100"),
            currency="RUB",
            description="test",
            return_url="https://app.example/subscription",
            idempotence_key="key-3",
            metadata={},
            client=_client(handler),
        )


async def test_create_payment_rejects_missing_link(monkeypatch):
    _authed_env(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "yk-no-link"})

    with pytest.raises(yookassa.YooKassaError):
        await yookassa.create_payment(
            amount=Decimal("100"),
            currency="RUB",
            description="test",
            return_url="https://app.example/subscription",
            idempotence_key="key-4",
            metadata={},
            client=_client(handler),
        )


async def test_create_payment_without_credentials_raises(monkeypatch):
    monkeypatch.delenv("YOOKASSA_SHOP_ID", raising=False)
    monkeypatch.delenv("YOOKASSA_SECRET_KEY", raising=False)

    with pytest.raises(yookassa.YooKassaError):
        await yookassa.create_payment(
            amount=Decimal("100"),
            currency="RUB",
            description="test",
            return_url="https://app.example/subscription",
            idempotence_key="key-5",
            metadata={},
            client=_client(lambda request: httpx.Response(200, json=_success_body())),
        )


async def test_create_payment_wraps_transport_errors(monkeypatch):
    _authed_env(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with pytest.raises(yookassa.YooKassaError):
        await yookassa.create_payment(
            amount=Decimal("100"),
            currency="RUB",
            description="test",
            return_url="https://app.example/subscription",
            idempotence_key="key-6",
            metadata={},
            client=_client(handler),
        )
