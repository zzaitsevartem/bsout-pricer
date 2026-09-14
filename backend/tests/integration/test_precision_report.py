import pytest

from src.modules.catalog.model.catalog import Brand, Device, PartType, QualityTier
from src.modules.products.model.product import Cluster, Product, StoreOffer
from src.modules.products.service.matching_service import MatchingService
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration


async def _fixture(db, offer_title: str, device_name: str, status: str = "auto") -> StoreOffer:
    brand = Brand(name="Xiaomi", slug="xiaomi")
    db.add(brand)
    await db.flush()

    device = Device(
        brand_id=brand.id, name=device_name, model_key=device_name.lower().replace(" ", "-")
    )
    part = PartType(code="display", name_ru="Дисплей")
    tier = QualityTier(code="copy", name_ru="Копия", rank=10)
    db.add_all([device, part, tier])
    await db.flush()

    cluster = Cluster(device_id=device.id, part_type_id=part.id)
    db.add(cluster)
    await db.flush()

    product = Product(
        cluster_id=cluster.id,
        quality_tier_id=tier.id,
        brand_id=brand.id,
        canonical_key=f"{device.model_key}|display|copy|-",
        canonical_name=f"Дисплей {device_name}",
    )
    store = Store(name="Тест", slug="test-store", website_url="http://t.example", is_active=True)
    db.add_all([product, store])
    await db.flush()

    offer = StoreOffer(
        store_id=store.id,
        product_id=product.id,
        source_sku="SKU-1",
        title=offer_title,
        normalized_title=offer_title.lower(),
        price_retail=1000,
        stock_status="in_stock",
        url="http://t.example/1",
        is_active=True,
        match_status=status,
    )
    db.add(offer)
    await db.flush()
    return offer


async def test_report_flags_offer_whose_title_has_a_suffix_the_device_lacks(db_session):
    await _fixture(db_session, "Дисплей для Xiaomi POCO X3 Pro", "POCO X3")

    rows = await MatchingService.precision_report(db_session)

    assert len(rows) == 1
    assert rows[0]["device"] == "POCO X3"
    assert rows[0]["missing"] == ["pro"]
    assert "X3 Pro" in rows[0]["title"]


async def test_report_stays_silent_when_device_matches_the_suffix(db_session):
    await _fixture(db_session, "Дисплей для Xiaomi POCO X3 Pro", "POCO X3 Pro")

    assert await MatchingService.precision_report(db_session) == []


async def test_report_ignores_offers_that_are_not_auto_matched(db_session):
    await _fixture(db_session, "Дисплей для Xiaomi POCO X3 Pro", "POCO X3", status="review")

    assert await MatchingService.precision_report(db_session) == []


async def test_report_collects_several_missing_suffixes(db_session):
    await _fixture(db_session, "Дисплей Poco X3 NFC / X3 Pro", "POCO X3")

    rows = await MatchingService.precision_report(db_session)

    assert rows[0]["missing"] == ["nfc", "pro"]


async def test_stats_report_share_of_suspicious_matches(db_session):
    await _fixture(db_session, "Дисплей для Xiaomi POCO X3 Pro", "POCO X3")

    stats = await MatchingService.precision_stats(db_session)

    assert stats["auto"] == 1
    assert stats["suspicious"] == 1
    assert stats["share_pct"] == 100.0


async def test_stats_are_zero_on_an_empty_catalogue(db_session):
    stats = await MatchingService.precision_stats(db_session)

    assert stats == {"auto": 0, "suspicious": 0, "share_pct": 0.0}
