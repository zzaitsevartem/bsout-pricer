import pytest
from sqlalchemy import func, select

from src.modules.catalog.model.catalog import (
    Brand,
    Color,
    ColorSynonym,
    Device,
    DeviceAlias,
    PartType,
    PartTypeSynonym,
    QualityTier,
    QualityTierSynonym,
    Stopword,
)
from src.modules.catalog.service.seed import (
    BRANDS,
    CATEGORIES,
    COLORS,
    DEVICES,
    PART_TYPES,
    QUALITY_TIERS,
    STOPWORDS,
    STORES,
    seed_all,
    seed_catalog,
    seed_categories,
    seed_stores,
)
from src.modules.categories.model.category import Category
from src.modules.stores.model.store import Store

pytestmark = pytest.mark.integration

_MODELS = [
    Brand,
    Device,
    DeviceAlias,
    PartType,
    PartTypeSynonym,
    QualityTier,
    QualityTierSynonym,
    Color,
    ColorSynonym,
    Stopword,
    Store,
    Category,
]


async def _counts(db) -> dict[str, int]:
    result = {}
    for model in _MODELS:
        result[model.__name__] = (
            await db.execute(select(func.count()).select_from(model))
        ).scalar()
    return result


async def test_seed_all_is_idempotent(db_session):
    await seed_all(db_session)
    first = await _counts(db_session)

    await seed_all(db_session)
    second = await _counts(db_session)

    assert first == second


async def test_seed_all_covers_expected_volume(db_session):
    await seed_all(db_session)
    counts = await _counts(db_session)

    assert counts["PartType"] == len(PART_TYPES)
    assert counts["QualityTier"] == len(QUALITY_TIERS)
    assert counts["Brand"] == len(BRANDS) == 10
    assert counts["Device"] == len(DEVICES)
    assert counts["Device"] >= 40
    assert counts["Color"] == len(COLORS)
    assert counts["Stopword"] == len(STOPWORDS)
    assert counts["Store"] == len(STORES) == 5
    assert counts["Category"] == len(CATEGORIES)
    assert counts["DeviceAlias"] == sum(len(aliases) for *_, aliases in DEVICES)


async def test_device_aliases_have_no_collisions(db_session):
    await seed_catalog(db_session)

    source_aliases = [alias for *_, aliases in DEVICES for alias in aliases]
    normalized = [alias.lower() for alias in source_aliases]
    assert len(normalized) == len(set(normalized))

    stored = (await db_session.execute(select(DeviceAlias.alias))).scalars().all()
    assert len(stored) == len(source_aliases)
    assert {alias.lower() for alias in stored} == set(normalized)


async def test_every_device_has_at_least_two_aliases(db_session):
    await seed_catalog(db_session)

    rows = (
        await db_session.execute(
            select(Device.model_key, func.count(DeviceAlias.id))
            .join(DeviceAlias, DeviceAlias.device_id == Device.id)
            .group_by(Device.model_key)
        )
    ).all()

    assert len(rows) == len(DEVICES)
    for model_key, alias_count in rows:
        assert alias_count >= 2, model_key


async def test_device_model_keys_are_brand_prefixed(db_session):
    await seed_catalog(db_session)

    rows = (
        await db_session.execute(
            select(Brand.slug, Device.model_key).join(Device, Device.brand_id == Brand.id)
        )
    ).all()

    assert len(rows) == len(DEVICES)
    for brand_slug, model_key in rows:
        assert model_key.startswith(f"{brand_slug}-"), model_key


async def test_alias_lookup_is_case_insensitive(db_session):
    await seed_catalog(db_session)

    device = (
        await db_session.execute(
            select(Device).join(DeviceAlias).where(DeviceAlias.alias == "АЙФОН 13")
        )
    ).scalar_one()

    assert device.model_key == "apple-iphone-13"


async def test_stores_seeded_with_expected_slugs(db_session):
    await seed_stores(db_session)

    stores = {
        slug: (name, url)
        for slug, name, url in (
            await db_session.execute(select(Store.slug, Store.name, Store.website_url))
        ).all()
    }

    assert set(stores) == {"tgsm", "profi", "liberti", "greenspark", "divizion"}
    assert stores["tgsm"] == ("ТГСМ", "https://taggsm.ru")
    assert stores["profi"] == ("Профи", "https://siriust.ru")

    active = (
        await db_session.execute(select(func.count()).select_from(Store).where(Store.is_active))
    ).scalar()
    assert active == len(STORES)


async def test_categories_seeded(db_session):
    await seed_categories(db_session)

    names = set((await db_session.execute(select(Category.name))).scalars().all())

    assert "Дисплеи" in names
    assert "Аккумуляторы" in names
    assert names == {name for _, name in CATEGORIES}


async def test_colors_and_synonyms_seeded(db_session):
    await seed_catalog(db_session)

    codes = set((await db_session.execute(select(Color.code))).scalars().all())
    assert {"black", "white", "gray", "gold"} <= codes

    synonyms = (await db_session.execute(select(ColorSynonym.synonym))).scalars().all()
    assert len(synonyms) == sum(len(syn) for _, syn in COLORS.values())
    assert len({s.lower() for s in synonyms}) == len(synonyms)


async def test_stopwords_seeded_without_quality_markers(db_session):
    await seed_catalog(db_session)

    words = {w.lower() for w in (await db_session.execute(select(Stopword.word))).scalars().all()}

    assert {"для", "в", "на", "с"} <= words
    assert "оригинал" not in words
    assert "копия" not in words


async def test_part_type_and_quality_synonyms_are_globally_unique(db_session):
    await seed_catalog(db_session)

    part_syn = (await db_session.execute(select(PartTypeSynonym.synonym))).scalars().all()
    assert len(part_syn) == sum(len(syn) for _, syn in PART_TYPES.values())
    assert len({s.lower() for s in part_syn}) == len(part_syn)

    quality_syn = (await db_session.execute(select(QualityTierSynonym.synonym))).scalars().all()
    assert len(quality_syn) == sum(len(syn) for _, _, syn in QUALITY_TIERS.values())
    assert len({s.lower() for s in quality_syn}) == len(quality_syn)


async def test_partial_reseed_after_manual_delete_restores_rows(db_session):
    await seed_all(db_session)
    before = await _counts(db_session)

    device = (
        await db_session.execute(select(Device).where(Device.model_key == "apple-iphone-15-pro"))
    ).scalar_one()
    await db_session.delete(device)
    await db_session.flush()

    await seed_all(db_session)
    after = await _counts(db_session)

    assert after == before
