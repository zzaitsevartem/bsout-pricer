from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.modules.products.controller import products

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("offer_count", [0, 3, 100])
async def test_offer_search_batches_store_lookup_and_preserves_response(monkeypatch, offer_count):
    now = datetime.now(timezone.utc)
    offers = [
        SimpleNamespace(
            id=index + 1,
            store_id=(index % 2) + 1,
            category_id=None,
            product_id=None,
            source_sku=str(index),
            title=f"Offer {index}",
            description=None,
            image_url=None,
            price_retail=Decimal(index % 2 + 10),
            price_opt=None,
            price_old=None,
            currency="RUB",
            stock_status="in_stock",
            stock_qty=None,
            url=f"https://example.com/{index}",
            last_seen_at=now,
        )
        for index in range(offer_count)
    ]
    stores = [
        SimpleNamespace(id=2, name="Second", slug="second"),
        SimpleNamespace(id=1, name="First", slug="first"),
    ]
    result = Mock()
    result.scalars.return_value.all.return_value = stores
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    search = AsyncMock(return_value=(offers, offer_count))
    record = AsyncMock()
    monkeypatch.setattr(products.ProductService, "search", search)
    monkeypatch.setattr(products, "is_fuzzy_enabled", AsyncMock(return_value=True))
    monkeypatch.setattr(products.SearchHistoryService, "record", record)
    response = await products.search_products(
        q=" display ",
        store=None,
        category=None,
        min_price=None,
        max_price=None,
        in_stock=None,
        sort_by="price_asc",
        page=1,
        per_page=100,
        db=db,
        user=SimpleNamespace(id=9),
    )
    assert db.execute.await_count == (1 if offers else 0)
    if offers:
        statement = db.execute.await_args.args[0]
        assert statement.compile().params == {"id_1": [1, 2]}
    assert response.total == offer_count
    assert response.page == 1
    assert response.per_page == 100
    assert [item.id for item in response.results] == [offer.id for offer in offers]
    for item, offer in zip(response.results, offers, strict=True):
        assert item.store.id == offer.store_id
        assert item.store.slug == ("first" if offer.store_id == 1 else "second")
        assert item.is_cheapest == (offer.price_retail == Decimal("10"))
    search.assert_awaited_once_with(
        db=db,
        query=" display ",
        store_slug=None,
        category_slug=None,
        min_price=None,
        max_price=None,
        in_stock=None,
        sort_by="price_asc",
        page=1,
        per_page=100,
        fuzzy=True,
    )
    record.assert_awaited_once_with(
        db=db,
        user_id=9,
        query="display",
        filters={
            "store": None,
            "category": None,
            "min_price": None,
            "max_price": None,
            "in_stock": None,
            "fuzzy": True,
        },
        results_count=offer_count,
    )
