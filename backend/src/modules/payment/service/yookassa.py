import os
from decimal import Decimal

import httpx

from src.config import settings

YOOKASSA_API_URL = "https://api.yookassa.ru/v3/payments"
YOOKASSA_PROVIDER = "yookassa"
REQUEST_TIMEOUT = 10.0


class YooKassaError(RuntimeError):
    pass


def credentials() -> tuple[str, str] | None:
    shop_id = getattr(settings, "yookassa_shop_id", None) or os.getenv("YOOKASSA_SHOP_ID")
    secret_key = getattr(settings, "yookassa_secret_key", None) or os.getenv("YOOKASSA_SECRET_KEY")
    if not shop_id or not secret_key:
        return None
    return str(shop_id), str(secret_key)


def is_configured() -> bool:
    return credentials() is not None


def _client_factory() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=REQUEST_TIMEOUT)


async def create_payment(
    amount: Decimal,
    currency: str,
    description: str,
    return_url: str,
    idempotence_key: str,
    metadata: dict[str, str],
    client: httpx.AsyncClient | None = None,
) -> tuple[str, str]:
    creds = credentials()
    if creds is None:
        raise YooKassaError("payment provider is not configured")
    shop_id, secret_key = creds
    payload = {
        "amount": {"value": f"{amount:.2f}", "currency": currency},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": description,
        "metadata": metadata,
    }
    owned = client is None
    active = client if client is not None else _client_factory()
    try:
        try:
            response = await active.post(
                YOOKASSA_API_URL,
                json=payload,
                auth=httpx.BasicAuth(shop_id, secret_key),
                headers={"Idempotence-Key": idempotence_key},
            )
        except httpx.HTTPError as exc:
            raise YooKassaError(f"payment provider request failed: {exc}") from exc
        if response.status_code >= 400:
            raise YooKassaError(f"payment provider rejected request: {response.status_code}")
        try:
            body = response.json()
        except ValueError as exc:
            raise YooKassaError("payment provider returned invalid json") from exc
        provider_id = body.get("id") if isinstance(body, dict) else None
        confirmation = body.get("confirmation") if isinstance(body, dict) else None
        confirmation_url = (
            confirmation.get("confirmation_url") if isinstance(confirmation, dict) else None
        )
        if not provider_id or not confirmation_url:
            raise YooKassaError("payment provider response misses payment link")
        return str(provider_id), str(confirmation_url)
    finally:
        if owned:
            await active.aclose()


async def get_payment(
    provider_payment_id: str,
    client: httpx.AsyncClient | None = None,
) -> dict:
    creds = credentials()
    if creds is None:
        raise YooKassaError("payment provider is not configured")
    shop_id, secret_key = creds
    owned = client is None
    active = client if client is not None else _client_factory()
    try:
        try:
            response = await active.get(
                f"{YOOKASSA_API_URL}/{provider_payment_id}",
                auth=httpx.BasicAuth(shop_id, secret_key),
            )
        except httpx.HTTPError as exc:
            raise YooKassaError(f"payment provider request failed: {exc}") from exc
        if response.status_code == 404:
            raise YooKassaError("payment not found at provider")
        if response.status_code >= 400:
            raise YooKassaError(f"payment provider rejected request: {response.status_code}")
        try:
            body = response.json()
        except ValueError as exc:
            raise YooKassaError("payment provider returned invalid json") from exc
        if not isinstance(body, dict) or not body.get("id"):
            raise YooKassaError("payment provider returned invalid object")
        return body
    finally:
        if owned:
            await active.aclose()
