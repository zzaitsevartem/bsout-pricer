import json
from pathlib import Path

import pytest
from sqlalchemy import select

from src.modules.catalog.model.catalog import Device, PartType, QualityTier
from src.modules.catalog.service.dictionaries import Dictionaries, load_dictionaries
from src.modules.catalog.service.extractor import UNKNOWN_QUALITY_CODE, extract
from src.modules.catalog.service.normalizer import normalize
from src.modules.catalog.service.seed import BRANDS, COLORS, DEVICES, PART_TYPES, seed_catalog

pytestmark = pytest.mark.integration

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "demo_offers.json"


@pytest.fixture
async def dicts(db_session) -> Dictionaries:
    await seed_catalog(db_session)
    await db_session.flush()
    return await load_dictionaries(db_session)


async def test_load_dictionaries_on_empty_db_returns_empty_structure(db_session) -> None:
    loaded = await load_dictionaries(db_session)
    assert loaded.device_by_alias == {}
    assert loaded.part_type_by_synonym == {}
    assert loaded.quality_by_synonym == {}
    assert loaded.color_by_synonym == {}
    assert loaded.stopwords == frozenset()


async def test_load_dictionaries_covers_seeded_catalog(dicts: Dictionaries, db_session) -> None:
    devices = (await db_session.execute(select(Device))).scalars().all()
    part_types = (await db_session.execute(select(PartType))).scalars().all()
    tiers = (await db_session.execute(select(QualityTier))).scalars().all()

    assert len(dicts.device_model_key) == len(devices) == len(DEVICES)
    assert len(dicts.part_type_code) == len(part_types) == len(PART_TYPES)
    assert len(dicts.quality_code) == len(tiers)
    assert len(dicts.color_code) == len(COLORS)
    assert dicts.stopwords


async def test_dictionary_keys_are_normalized(dicts: Dictionaries) -> None:
    all_keys = [
        *dicts.device_by_alias,
        *dicts.part_type_by_synonym,
        *dicts.quality_by_synonym,
        *dicts.color_by_synonym,
        *dicts.stopwords,
    ]
    assert all_keys
    for key in all_keys:
        assert key == normalize(key)
        assert key == key.strip()
        assert "  " not in key


async def test_device_aliases_resolve_to_expected_devices(dicts: Dictionaries) -> None:
    for alias, expected_model_key in [
        ("iphone 13", "apple-iphone-13"),
        ("айфон 13", "apple-iphone-13"),
        ("ip13", "apple-iphone-13"),
        ("galaxy a12", "samsung-galaxy-a12"),
        ("sm a125", "samsung-galaxy-a12"),
        ("redmi note 12", "xiaomi-redmi-note-12"),
        ("poco x3", "xiaomi-poco-x3"),
        ("p30 lite", "huawei-p30-lite"),
    ]:
        device_id = dicts.device_by_alias[alias]
        assert dicts.device_model_key[device_id] == expected_model_key


async def test_brand_mapping_is_consistent(dicts: Dictionaries) -> None:
    assert set(dicts.device_brand) == set(dicts.device_model_key)
    assert len(set(dicts.device_brand.values())) == len(BRANDS)
    iphone_id = dicts.device_by_alias["iphone 13"]
    galaxy_id = dicts.device_by_alias["galaxy a12"]
    assert dicts.device_brand[iphone_id] != dicts.device_brand[galaxy_id]


async def test_part_type_and_quality_codes_are_present(dicts: Dictionaries) -> None:
    assert set(dicts.part_type_code.values()) == set(PART_TYPES)
    assert UNKNOWN_QUALITY_CODE in dicts.quality_code.values()
    assert dicts.quality_code[dicts.quality_by_synonym["копия"]] == "copy"
    assert dicts.quality_code[dicts.quality_by_synonym["оригинал"]] == "original"
    assert dicts.part_type_code[dicts.part_type_by_synonym["акб"]] == "battery"


async def test_load_dictionaries_is_idempotent(db_session) -> None:
    await seed_catalog(db_session)
    await db_session.flush()
    first = await load_dictionaries(db_session)
    second = await load_dictionaries(db_session)
    assert first.device_by_alias == second.device_by_alias
    assert first.part_type_by_synonym == second.part_type_by_synonym
    assert first.stopwords == second.stopwords


async def test_extract_with_db_loaded_dictionaries(dicts: Dictionaries) -> None:
    result = extract("Дисплей Apple iPhone 13 в сборе с тачскрином (Original)", dicts)
    assert dicts.device_model_key[result.device_id] == "apple-iphone-13"
    assert dicts.part_type_code[result.part_type_id] == "display"
    assert dicts.quality_code[result.quality_tier_id] == "original"
    assert result.brand_id == dicts.device_brand[result.device_id]
    assert result.confidence == pytest.approx(0.95)


async def test_demo_fixture_extraction_quality(dicts: Dictionaries) -> None:
    titles = [offer["title"] for offer in json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))]
    unknown_ids = {
        tier_id for tier_id, code in dicts.quality_code.items() if code == UNKNOWN_QUALITY_CODE
    }
    both = 0
    quality = 0
    for title in titles:
        result = extract(title, dicts)
        if result.device_id is not None and result.part_type_id is not None:
            both += 1
        if result.quality_tier_id not in unknown_ids:
            quality += 1
    assert both / len(titles) >= 0.95
    assert quality == len(titles)
