from decimal import Decimal

import pytest
from sqlalchemy import func, select

from src.modules.auth.model.user import User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.products.model.product import OfferPriceHistory, StoreOffer
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration

IMPORT_URL = "/api/admin/offers/import"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_store(db, slug: str = "tgsm", name: str = "ТГСМ") -> Store:
    store = Store(name=name, slug=slug, website_url="https://taggsm.ru", is_active=True)
    db.add(store)
    await db.flush()
    return store


async def _make_user(db, email: str, *, is_admin: bool) -> User:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Import User",
        is_active=True,
        is_admin=is_admin,
    )
    db.add(user)
    await db.flush()
    return user


async def _admin_headers(db, email: str = "import-admin@example.com") -> dict[str, str]:
    admin = await _make_user(db, email, is_admin=True)
    return _auth(create_access_token(admin.id))


def _row(**overrides) -> dict:
    row = {
        "store_slug": "tgsm",
        "source_sku": "TG-12345",
        "title": "Дисплей iPhone 13 (оригинал)",
        "price_retail": "4500.00",
        "price_opt": "3900.00",
        "price_old": None,
        "stock_status": "in_stock",
        "stock_qty": 3,
        "url": "https://taggsm.ru/p/12345",
        "image_url": None,
        "description": None,
        "category": None,
    }
    row.update(overrides)
    return row


async def _count(db, model) -> int:
    return (await db.execute(select(func.count()).select_from(model))).scalar()


async def test_import_creates_offers_and_reports_summary(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    payload = [
        _row(),
        _row(source_sku="TG-777", title="Аккумулятор iPhone 12", price_retail="1200.50"),
    ]

    resp = await client.post(IMPORT_URL, json=payload, headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body == {"total": 2, "created": 2, "updated": 0, "skipped": 0, "errors": []}

    offers = (
        (await db_session.execute(select(StoreOffer).order_by(StoreOffer.source_sku)))
        .scalars()
        .all()
    )
    assert [offer.source_sku for offer in offers] == ["TG-12345", "TG-777"]
    assert offers[0].store_id == store.id
    assert offers[0].price_retail == Decimal("4500.00")
    assert offers[0].price_opt == Decimal("3900.00")
    assert offers[0].stock_status == "in_stock"
    assert offers[0].stock_qty == 3
    assert offers[0].normalized_title == "дисплей iphone 13 оригинал"
    assert offers[0].is_active is True
    assert await _count(db_session, OfferPriceHistory) == 2


async def test_repeated_import_is_idempotent(client, db_session):
    await _make_store(db_session)
    headers = await _admin_headers(db_session)
    payload = [_row(), _row(source_sku="TG-777", title="Аккумулятор", price_retail="1200.00")]

    first = await client.post(IMPORT_URL, json=payload, headers=headers)
    second = await client.post(IMPORT_URL, json=payload, headers=headers)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["created"] == 2
    assert second.json() == {"total": 2, "created": 0, "updated": 2, "skipped": 0, "errors": []}

    assert await _count(db_session, StoreOffer) == 2
    assert await _count(db_session, OfferPriceHistory) == 2


async def test_price_change_records_history_and_updates_offer(client, db_session):
    await _make_store(db_session)
    headers = await _admin_headers(db_session)

    await client.post(IMPORT_URL, json=[_row()], headers=headers)
    resp = await client.post(
        IMPORT_URL,
        json=[_row(price_retail="4900.00", stock_status="low", stock_qty=1)],
        headers=headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["updated"] == 1
    assert resp.json()["created"] == 0

    offer = (await db_session.execute(select(StoreOffer))).scalar_one()
    assert offer.price_retail == Decimal("4900.00")
    assert offer.stock_status == "low"
    assert offer.stock_qty == 1
    assert offer.price_changed_at is not None

    history = (
        (
            await db_session.execute(
                select(OfferPriceHistory)
                .where(OfferPriceHistory.offer_id == offer.id)
                .order_by(OfferPriceHistory.id)
            )
        )
        .scalars()
        .all()
    )
    assert [entry.price_retail for entry in history] == [Decimal("4500.00"), Decimal("4900.00")]


async def test_unknown_store_slug_is_reported_not_fatal(client, db_session):
    await _make_store(db_session)
    headers = await _admin_headers(db_session)

    resp = await client.post(
        IMPORT_URL,
        json=[_row(store_slug="nonexistent", source_sku="NX-1")],
        headers=headers,
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["created"] == 0
    assert body["updated"] == 0
    assert body["skipped"] == 1
    assert body["errors"][0]["index"] == 0
    assert body["errors"][0]["store_slug"] == "nonexistent"
    assert "not found" in body["errors"][0]["reason"]
    assert await _count(db_session, StoreOffer) == 0


@pytest.mark.parametrize("bad_price", ["0", "-100.00", "abc", None])
async def test_invalid_price_is_rejected_per_row(client, db_session, bad_price):
    await _make_store(db_session)
    headers = await _admin_headers(db_session)

    resp = await client.post(IMPORT_URL, json=[_row(price_retail=bad_price)], headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["created"] == 0
    assert body["skipped"] == 1
    assert body["errors"][0]["index"] == 0
    assert "price_retail" in body["errors"][0]["reason"]
    assert await _count(db_session, StoreOffer) == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"stock_status": "totally_invalid"},
        {"source_sku": "   "},
        {"title": ""},
        {"store_slug": ""},
    ],
)
async def test_invalid_field_values_are_rejected_per_row(client, db_session, overrides):
    await _make_store(db_session)
    headers = await _admin_headers(db_session)

    resp = await client.post(IMPORT_URL, json=[_row(**overrides)], headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["skipped"] == 1
    assert body["created"] == 0
    assert body["errors"][0]["index"] == 0
    assert await _count(db_session, StoreOffer) == 0


async def test_partial_success_keeps_good_rows(client, db_session):
    await _make_store(db_session)
    headers = await _admin_headers(db_session)
    payload = [
        _row(source_sku="OK-1"),
        _row(source_sku="BAD-1", price_retail="-1"),
        _row(source_sku="BAD-2", store_slug="ghost-store"),
        _row(source_sku="OK-2", title="Стекло iPhone 14", price_retail="800.00"),
        "not-an-object",
    ]

    resp = await client.post(IMPORT_URL, json=payload, headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 5
    assert body["created"] == 2
    assert body["updated"] == 0
    assert body["skipped"] == 3
    assert [error["index"] for error in body["errors"]] == [1, 2, 4]

    skus = (
        (await db_session.execute(select(StoreOffer.source_sku).order_by(StoreOffer.source_sku)))
        .scalars()
        .all()
    )
    assert list(skus) == ["OK-1", "OK-2"]


async def test_duplicate_sku_within_one_batch_upserts_once(client, db_session):
    await _make_store(db_session)
    headers = await _admin_headers(db_session)

    resp = await client.post(
        IMPORT_URL,
        json=[_row(), _row(price_retail="5000.00")],
        headers=headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["created"] == 1
    assert resp.json()["updated"] == 1
    assert await _count(db_session, StoreOffer) == 1

    offer = (await db_session.execute(select(StoreOffer))).scalar_one()
    assert offer.price_retail == Decimal("5000.00")


async def test_empty_payload_returns_zero_summary(client, db_session):
    await _make_store(db_session)
    headers = await _admin_headers(db_session)

    resp = await client.post(IMPORT_URL, json=[], headers=headers)

    assert resp.status_code == 200, resp.text
    assert resp.json() == {"total": 0, "created": 0, "updated": 0, "skipped": 0, "errors": []}


async def test_non_admin_gets_403(client, db_session):
    await _make_store(db_session)
    user = await _make_user(db_session, "plain@example.com", is_admin=False)

    resp = await client.post(IMPORT_URL, json=[_row()], headers=_auth(create_access_token(user.id)))

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Admin access required"
    assert await _count(db_session, StoreOffer) == 0


async def test_anonymous_request_is_rejected(client, db_session):
    await _make_store(db_session)

    resp = await client.post(IMPORT_URL, json=[_row()])

    assert resp.status_code == 403
    assert await _count(db_session, StoreOffer) == 0
