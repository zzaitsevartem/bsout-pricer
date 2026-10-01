import json
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select

from src.modules.catalog.service.dictionaries import load_dictionaries
from src.modules.catalog.service.seed import seed_all
from src.modules.parser.service.base import ParseResult
from src.modules.parser.service.parser_service import ParserService
from src.modules.products.model.product import Cluster, MatchCandidate, Product, StoreOffer
from src.modules.products.service.matching_service import MatchingService, MatchStats
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "demo_offers.json"

GROUND_TRUTH_GROUPS = {
    "apple-iphone-13|display|original|-": 5,
    "apple-iphone-13|battery|original|-": 5,
    "apple-iphone-11|display|copy|-": 5,
    "xiaomi-redmi-note-12|display|copy|-": 5,
}

IPHONE_13_DISPLAY_TIERS = {
    "apple-iphone-13|display|original|-",
    "apple-iphone-13|display|service|-",
    "apple-iphone-13|display|oem_hq|-",
    "apple-iphone-13|display|copy|-",
}


async def _seed_and_import(db) -> int:
    await seed_all(db)
    rows = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    store_ids = {
        slug: store_id for slug, store_id in (await db.execute(select(Store.slug, Store.id))).all()
    }
    for row in rows:
        await ParserService.upsert_offer(
            db,
            store_ids[row["store_slug"]],
            ParseResult(
                source_sku=row["source_sku"],
                title=row["title"],
                price_retail=Decimal(row["price_retail"]),
                price_opt=Decimal(row["price_opt"]) if row.get("price_opt") else None,
                price_old=Decimal(row["price_old"]) if row.get("price_old") else None,
                stock_status=row["stock_status"],
                stock_qty=row.get("stock_qty"),
                url=row["url"],
            ),
        )
    return len(rows)


async def _stores_for(db, canonical_key: str) -> int:
    return (
        await db.execute(
            select(func.count(func.distinct(StoreOffer.store_id)))
            .select_from(StoreOffer)
            .join(Product, Product.id == StoreOffer.product_id)
            .where(Product.canonical_key == canonical_key)
        )
    ).scalar()


async def test_ground_truth_groups_collapse_into_one_product(db_session):
    total = await _seed_and_import(db_session)
    stats = await MatchingService.match_all(db_session)

    assert stats["processed"] == total
    assert stats["unmatched"] == 0

    for canonical_key, expected_stores in GROUND_TRUTH_GROUPS.items():
        product_count = (
            await db_session.execute(
                select(func.count())
                .select_from(Product)
                .where(Product.canonical_key == canonical_key)
            )
        ).scalar()
        assert product_count == 1, canonical_key
        assert await _stores_for(db_session, canonical_key) == expected_stores, canonical_key


async def test_quality_tiers_are_not_merged(db_session):
    await _seed_and_import(db_session)
    await MatchingService.match_all(db_session)

    keys = set(
        (
            await db_session.execute(
                select(Product.canonical_key).where(
                    Product.canonical_key.like("apple-iphone-13|display|%")
                )
            )
        )
        .scalars()
        .all()
    )

    assert IPHONE_13_DISPLAY_TIERS <= keys


async def test_all_tiers_share_one_cluster(db_session):
    await _seed_and_import(db_session)
    await MatchingService.match_all(db_session)

    cluster_ids = set(
        (
            await db_session.execute(
                select(Product.cluster_id).where(Product.canonical_key.in_(IPHONE_13_DISPLAY_TIERS))
            )
        )
        .scalars()
        .all()
    )

    assert len(cluster_ids) == 1


async def test_cluster_aggregates_are_recalculated(db_session):
    await _seed_and_import(db_session)
    await MatchingService.match_all(db_session)

    cluster_id = (
        await db_session.execute(
            select(Product.cluster_id).where(
                Product.canonical_key == "apple-iphone-13|display|original|-"
            )
        )
    ).scalar_one()
    cluster = (
        await db_session.execute(select(Cluster).where(Cluster.id == cluster_id))
    ).scalar_one()

    offers_in_cluster = (
        await db_session.execute(
            select(func.count(), func.min(StoreOffer.price_retail))
            .select_from(StoreOffer)
            .join(Product, Product.id == StoreOffer.product_id)
            .where(Product.cluster_id == cluster_id, StoreOffer.is_active.is_(True))
        )
    ).one()

    assert cluster.offers_count == offers_in_cluster[0]
    assert cluster.min_price_retail == offers_in_cluster[1]


async def test_matching_is_idempotent(db_session):
    await _seed_and_import(db_session)
    first = await MatchingService.match_all(db_session)

    products_after_first = (
        await db_session.execute(select(func.count()).select_from(Product))
    ).scalar()

    second = await MatchingService.match_all(db_session)
    products_after_second = (
        await db_session.execute(select(func.count()).select_from(Product))
    ).scalar()

    assert first["auto"] > 0
    assert second["processed"] == 0
    assert products_after_first == products_after_second


async def test_manual_and_rejected_decisions_are_preserved(db_session):
    await _seed_and_import(db_session)
    await MatchingService.match_all(db_session)

    offer = (
        await db_session.execute(select(StoreOffer).order_by(StoreOffer.id).limit(1))
    ).scalar_one()
    offer.match_status = "manual"
    offer.product_id = None
    await db_session.flush()

    rejected = (
        await db_session.execute(select(StoreOffer).order_by(StoreOffer.id).offset(1).limit(1))
    ).scalar_one()
    rejected.match_status = "rejected"
    rejected.product_id = None
    await db_session.flush()

    await MatchingService.match_all(db_session, only_unmatched=True)

    await db_session.refresh(offer)
    await db_session.refresh(rejected)
    assert offer.match_status == "manual"
    assert offer.product_id is None
    assert rejected.match_status == "rejected"
    assert rejected.product_id is None


async def test_low_confidence_offer_goes_to_moderation_queue(db_session):
    await seed_all(db_session)
    store = (await db_session.execute(select(Store).limit(1))).scalar_one()

    await ParserService.upsert_offer(
        db_session,
        store.id,
        ParseResult(
            source_sku="NOISE-1",
            title="Универсальный набор отвёрток",
            price_retail=Decimal("500.00"),
            url="http://example.com/noise",
        ),
    )
    stats = await MatchingService.match_all(db_session)

    assert stats["auto"] == 0
    assert stats["unmatched"] == 1
    assert (
        await db_session.execute(select(func.count()).select_from(MatchCandidate))
    ).scalar() == 0


async def test_known_part_unknown_device_routes_to_review(db_session):
    await seed_all(db_session)
    store = Store(name="ReviewTest", slug="review-test", website_url="https://rt.example")
    db_session.add(store)
    await db_session.flush()

    offer = await ParserService.upsert_offer(
        db_session,
        store.id,
        ParseResult(
            source_sku="RV1",
            title="Дисплей для Blackberry Passport (копия)",
            price_retail=Decimal("1000.00"),
            url="https://rt.example/1",
        ),
    )

    dicts = await load_dictionaries(db_session)
    stats = MatchStats()
    outcome = await MatchingService.match_offer(db_session, offer, dicts, stats)

    assert outcome.status == "review"
    assert outcome.product_id is None
    assert offer.match_status == "review"
    assert offer.product_id is None
    assert stats.review == 1
    assert stats.unmatched == 0


async def test_device_gap_report_surfaces_review_offers(db_session):
    await seed_all(db_session)
    store = Store(name="GapTest", slug="gap-test", website_url="https://gt.example")
    db_session.add(store)
    await db_session.flush()

    offer = await ParserService.upsert_offer(
        db_session,
        store.id,
        ParseResult(
            source_sku="G1",
            title="Дисплей для Blackberry Passport (копия)",
            price_retail=Decimal("1000.00"),
            url="https://gt.example/1",
        ),
    )
    dicts = await load_dictionaries(db_session)
    await MatchingService.match_offer(db_session, offer, dicts, MatchStats())

    report = await MatchingService.device_gap_report(db_session, limit=10)

    assert ("Blackberry Passport", 1) in report
