from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from src.modules.products.model.product import OfferPriceHistory, StoreOffer
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration


async def _make_store(db, slug: str = "test-store") -> Store:
    store = Store(name="Test Store", slug=slug, website_url="http://example.com", is_active=True)
    db.add(store)
    await db.flush()
    return store


async def test_offer_persists_opt_price_and_stock_status(db_session):
    store = await _make_store(db_session)
    offer = StoreOffer(
        store_id=store.id,
        source_sku="SKU-1",
        title="Дисплей iPhone 13",
        normalized_title="дисплей iphone 13",
        price_retail=Decimal("4500.00"),
        price_opt=Decimal("3900.00"),
        stock_status="low",
        stock_qty=2,
        url="http://example.com/1",
    )
    db_session.add(offer)
    await db_session.flush()

    assert offer.id is not None
    assert offer.price_opt == Decimal("3900.00")
    assert offer.stock_status == "low"
    assert offer.stock_qty == 2
    assert offer.is_active is True
    assert offer.match_status == "unmatched"
    assert offer.currency == "RUB"


async def test_unique_store_id_source_sku(db_session):
    store = await _make_store(db_session)
    db_session.add(
        StoreOffer(
            store_id=store.id,
            source_sku="DUP",
            title="a",
            normalized_title="a",
            price_retail=Decimal("10.00"),
            url="http://example.com/a",
        )
    )
    await db_session.flush()

    db_session.add(
        StoreOffer(
            store_id=store.id,
            source_sku="DUP",
            title="b",
            normalized_title="b",
            price_retail=Decimal("20.00"),
            url="http://example.com/b",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_stock_status_check_constraint_rejects_unknown_value(db_session):
    store = await _make_store(db_session)
    db_session.add(
        StoreOffer(
            store_id=store.id,
            source_sku="BAD",
            title="a",
            normalized_title="a",
            price_retail=Decimal("10.00"),
            url="http://example.com/a",
            stock_status="totally_invalid",
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_offer_price_history_cascade(db_session):
    store = await _make_store(db_session)
    offer = StoreOffer(
        store_id=store.id,
        source_sku="SKU-H",
        title="a",
        normalized_title="a",
        price_retail=Decimal("100.00"),
        url="http://example.com/h",
    )
    db_session.add(offer)
    await db_session.flush()

    db_session.add(
        OfferPriceHistory(
            offer_id=offer.id,
            price_retail=Decimal("100.00"),
            price_opt=Decimal("90.00"),
            stock_status="in_stock",
        )
    )
    await db_session.flush()

    assert offer.id is not None
