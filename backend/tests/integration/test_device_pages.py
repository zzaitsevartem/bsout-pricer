from decimal import Decimal

import pytest
from sqlalchemy import select

from src.modules.catalog.model.catalog import Device, DeviceAlias
from src.modules.catalog.schema.device import DeviceMetadata
from src.modules.catalog.service.device_metadata import import_metadata
from src.modules.products.service.comparison_service import ComparisonService
from tests.integration.test_comparison_api import (
    _make_dictionaries,
    _make_offer,
    _make_product,
    _make_store,
)

pytestmark = pytest.mark.integration


async def test_device_detail_missing_and_empty_metadata(client, db_session):
    assert (await client.get("/api/devices/absent")).status_code == 404
    refs = await _make_dictionaries(db_session)
    response = await client.get(f"/api/devices/{refs['device'].model_key}")
    assert response.status_code == 200
    body = response.json()
    assert body["brand"]["slug"] == "apple"
    assert body["images"] == []
    assert body["release_year"] is None
    assert body["model_codes"] == []


async def test_metadata_import_exact_identity_repeatability_and_code_search(client, db_session):
    refs = await _make_dictionaries(db_session)
    await _make_product(db_session, refs, refs["tier_copy"], "one", "Display")
    db_session.add(
        Device(brand_id=refs["brand"].id, name="iPhone 13 mini", model_key="apple-iphone-13-mini")
    )
    await db_session.flush()
    record = DeviceMetadata.model_validate(
        {
            "model_key": refs["device"].model_key,
            "release_year": 2021,
            "model_codes": ["A2633"],
            "metadata_source_url": "https://apple.com/iphone",
            "images": [
                {
                    "url": "https://apple.com/photo.jpg",
                    "source_name": "Apple",
                    "source_url": "https://apple.com/iphone",
                }
            ],
        }
    )
    assert (await import_metadata(db_session, [record]))["updated"] == 1
    assert (await import_metadata(db_session, [record]))["updated"] == 0
    aliases = (await db_session.scalars(select(DeviceAlias))).all()
    assert len(aliases) == 1
    suggestions = await ComparisonService.device_suggestions(db_session, "Apple A2633")
    assert [item["model_key"] for item in suggestions] == ["apple-iphone-13"]
    body = (await client.get("/api/devices/apple-iphone-13")).json()
    assert body["release_year"] == 2021
    assert body["images"][0]["source_name"] == "Apple"
    assert (await client.get("/api/devices/apple-iphone-13-mini")).json()["images"] == []


async def test_device_facets_total_ignores_category_and_counts_canonical_products(db_session):
    from src.modules.catalog.model.catalog import PartType
    from src.modules.products.model.product import Cluster

    refs = await _make_dictionaries(db_session)
    first = await _make_product(db_session, refs, refs["tier_copy"], "one", "Display")
    store = await _make_store(db_session, "device-store")
    await _make_offer(db_session, store, first, "one", "100")
    await _make_offer(db_session, store, first, "two", "110")
    battery = PartType(code="battery", name_ru="Аккумуляторы")
    db_session.add(battery)
    await db_session.flush()
    cluster = Cluster(device_id=refs["device"].id, part_type_id=battery.id)
    db_session.add(cluster)
    await db_session.flush()
    refs["cluster"] = cluster
    second = await _make_product(db_session, refs, refs["tier_copy"], "two", "Battery")
    await _make_offer(db_session, store, second, "three", "200", stock_status="out")
    facets = await ComparisonService.catalog_facets(
        db_session,
        device_id=refs["device"].id,
        part_type_id=refs["part_type"].id,
        quality_tier_id=refs["tier_copy"].id,
        store_slug=store.slug,
    )
    assert facets["total"] == 2
    assert {item["count"] for item in facets["part_types"]} == {1}
    available = await ComparisonService.catalog_facets(
        db_session,
        device_id=refs["device"].id,
        in_stock=True,
        store_slug=store.slug,
        quality_tier_id=refs["tier_copy"].id,
        part_type_id=battery.id,
        min_price=Decimal("100"),
        max_price=Decimal("110"),
    )
    assert available["total"] == 1
    assert {item["id"]: item["count"] for item in available["part_types"]} == {
        refs["part_type"].id: 1,
        battery.id: 0,
    }


async def test_import_does_not_create_unknown_models_or_steal_aliases(db_session):
    refs = await _make_dictionaries(db_session)
    neighbor = Device(
        brand_id=refs["brand"].id, name="iPhone 13 mini", model_key="apple-iphone-13-mini"
    )
    db_session.add(neighbor)
    await db_session.flush()
    db_session.add(DeviceAlias(device_id=neighbor.id, alias="SHARED", source="verified"))
    await db_session.flush()
    records = [
        DeviceMetadata.model_validate(
            {
                "model_key": key,
                "model_codes": ["SHARED"],
                "metadata_source_url": "https://example.org/device",
            }
        )
        for key in [refs["device"].model_key, "nonexistent"]
    ]
    result = await import_metadata(db_session, records)
    assert result["missing"] == ["nonexistent"]
    assert result["alias_conflicts"] == ["SHARED"]
    alias = await db_session.scalar(select(DeviceAlias).where(DeviceAlias.alias == "SHARED"))
    assert alias.device_id == neighbor.id
    assert await db_session.scalar(select(Device).where(Device.model_key == "nonexistent")) is None
