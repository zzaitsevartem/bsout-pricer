import json
from pathlib import Path

import pytest

from src.modules.catalog.service.dictionaries import Dictionaries
from src.modules.catalog.service.extractor import UNKNOWN_QUALITY_CODE, extract
from src.modules.catalog.service.normalizer import normalize
from src.modules.catalog.service.seed import (
    BRANDS,
    COLORS,
    DEVICES,
    PART_TYPES,
    QUALITY_TIERS,
    STOPWORDS,
)

pytestmark = pytest.mark.unit

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "demo_offers.json"


def _build_dictionaries() -> Dictionaries:
    brand_ids = {name: index + 1 for index, name in enumerate(BRANDS)}

    device_by_alias: dict[str, int] = {}
    device_model_key: dict[int, str] = {}
    device_brand: dict[int, int] = {}
    for index, (brand_name, device_name, model_key, aliases) in enumerate(DEVICES, start=1):
        device_model_key[index] = model_key
        device_brand[index] = brand_ids[brand_name]
        for raw in [model_key.replace("-", " "), device_name, *aliases]:
            key = normalize(raw)
            if key:
                device_by_alias.setdefault(key, index)

    part_type_by_synonym: dict[str, int] = {}
    part_type_code: dict[int, str] = {}
    for index, (code, (name_ru, synonyms)) in enumerate(PART_TYPES.items(), start=1):
        part_type_code[index] = code
        for raw in [name_ru, *synonyms]:
            key = normalize(raw)
            if key:
                part_type_by_synonym.setdefault(key, index)

    quality_by_synonym: dict[str, int] = {}
    quality_code: dict[int, str] = {}
    for index, (code, (_name_ru, _rank, synonyms)) in enumerate(QUALITY_TIERS.items(), start=1):
        quality_code[index] = code
        for raw in synonyms:
            key = normalize(raw)
            if key:
                quality_by_synonym.setdefault(key, index)

    color_by_synonym: dict[str, int] = {}
    color_code: dict[int, str] = {}
    for index, (code, (name_ru, synonyms)) in enumerate(COLORS.items(), start=1):
        color_code[index] = code
        for raw in [name_ru, *synonyms]:
            key = normalize(raw)
            if key:
                color_by_synonym.setdefault(key, index)

    return Dictionaries(
        device_by_alias=device_by_alias,
        device_model_key=device_model_key,
        device_brand=device_brand,
        part_type_by_synonym=part_type_by_synonym,
        part_type_code=part_type_code,
        quality_by_synonym=quality_by_synonym,
        quality_code=quality_code,
        color_by_synonym=color_by_synonym,
        color_code=color_code,
        stopwords=frozenset(normalize(word) for word in STOPWORDS),
    )


@pytest.fixture(scope="module")
def dicts() -> Dictionaries:
    return _build_dictionaries()


def _codes(
    title: str, dicts: Dictionaries
) -> tuple[str | None, str | None, str | None, str | None]:
    result = extract(title, dicts)
    return (
        dicts.device_model_key.get(result.device_id) if result.device_id else None,
        dicts.part_type_code.get(result.part_type_id) if result.part_type_id else None,
        dicts.quality_code.get(result.quality_tier_id) if result.quality_tier_id else None,
        dicts.color_code.get(result.color_id) if result.color_id else None,
    )


SYNTHETIC_CASES = [
    (
        "Дисплей Apple iPhone 13 в сборе с тачскрином (Original)",
        ("apple-iphone-13", "display", "original", None),
    ),
    ("Дисплей для iPhone 13 + тачскрин копия", ("apple-iphone-13", "display", "copy", None)),
    ("Тачскрин iPhone 13 копия", ("apple-iphone-13", "touchscreen", "copy", None)),
    ("АКБ для iPhone 11 ориг", ("apple-iphone-11", "battery", "original", None)),
    ("Крышки задние для iPhone 15 оригинал", ("apple-iphone-15", "back_cover", "original", None)),
    ("Стекло задней крышки iPhone 13 копия", ("apple-iphone-13", "back_cover", "copy", None)),
    ("Стекло дисплея Apple iPhone 12 (Копия)", ("apple-iphone-12", "glass", "copy", None)),
    (
        "Материнская плата для iPhone 12 сервисный",
        ("apple-iphone-12", "board", "service", None),
    ),
    ("Buzzer iPhone13 Copy AAA", ("apple-iphone-13", "speaker", "copy", None)),
    ("LCD iPhone13 + Touch OEM", ("apple-iphone-13", "display", "oem_hq", None)),
    ("Дисплей для SM-G991 (S21) ориг", ("samsung-galaxy-s21", "display", "original", None)),
    ("S23 Galaxy Samsung дисплей ORIG (OLED)", ("samsung-galaxy-s23", "display", "original", None)),
    (
        "Задняя крышка чёрная iPhone 13 оригинал",
        ("apple-iphone-13", "back_cover", "original", "black"),
    ),
    ("Аккумулятор Poco X5 синий копия", ("xiaomi-poco-x5", "battery", "copy", "blue")),
]


@pytest.mark.parametrize(("title", "expected"), SYNTHETIC_CASES)
def test_extract_synthetic_cases(title: str, expected: tuple, dicts: Dictionaries) -> None:
    assert _codes(title, dicts) == expected


LONGEST_DEVICE_CASES = [
    ("Дисплей для iPhone 13 копия", "apple-iphone-13"),
    ("Дисплей для iPhone 13 Pro копия", "apple-iphone-13-pro"),
    ("Дисплей для iPhone 13 Pro Max копия", "apple-iphone-13-pro-max"),
    ("Дисплей для iPhone 13 mini копия", "apple-iphone-13-mini"),
    ("Дисплей Samsung Galaxy S21 копия", "samsung-galaxy-s21"),
    ("Дисплей Samsung Galaxy S21 Ultra копия", "samsung-galaxy-s21-ultra"),
    ("Дисплей Xiaomi Redmi 10 копия", "xiaomi-redmi-10"),
    ("Дисплей Xiaomi Redmi Note 10 копия", "xiaomi-redmi-note-10"),
]


@pytest.mark.parametrize(("title", "expected"), LONGEST_DEVICE_CASES)
def test_longest_device_alias_wins(title: str, expected: str, dicts: Dictionaries) -> None:
    result = extract(title, dicts)
    assert dicts.device_model_key[result.device_id] == expected


def test_similar_model_names_are_not_confused(dicts: Dictionaries) -> None:
    assert _codes("Аккумулятор Honor X8 копия", dicts)[0] == "honor-x8"
    assert _codes("Аккумулятор Honor 9X копия", dicts)[0] == "honor-9x"
    assert _codes("Аккумулятор Honor 8X копия", dicts)[0] == "honor-8x"
    assert _codes("Дисплей Хонор 8Х в сборе копия", dicts)[0] == "honor-8x"


def test_cyrillic_and_latin_spellings_agree(dicts: Dictionaries) -> None:
    assert _codes("Дисплей Айфон 13 копия", dicts) == _codes("Дисплей iPhone 13 копия", dicts)
    assert _codes("Батарея Хуавей П30 Лайт копия", dicts) == _codes(
        "Battery Huawei P30 Lite Copy", dicts
    )
    assert _codes("Экран Редми Ноут 12 копия", dicts) == _codes(
        "Дисплей Redmi Note 12 копия", dicts
    )


def test_glued_model_numbers_are_split(dicts: Dictionaries) -> None:
    assert _codes("Main camera iPhone14 OEM", dicts)[0] == "apple-iphone-14"
    assert _codes("Glass Redmi Note12 (OCA) Copy AAA", dicts)[0] == "xiaomi-redmi-note-12"


def test_brand_is_derived_from_device(dicts: Dictionaries) -> None:
    result = extract("Дисплей Apple iPhone 13 копия", dicts)
    assert result.brand_id == dicts.device_brand[result.device_id]
    assert result.brand_id is not None


def test_unknown_quality_is_used_as_fallback(dicts: Dictionaries) -> None:
    result = extract("Дисплей Apple iPhone 13 в сборе", dicts)
    assert dicts.quality_code[result.quality_tier_id] == UNKNOWN_QUALITY_CODE
    assert "quality_tier" not in result.matched


def test_matched_reports_recognised_surface_forms(dicts: Dictionaries) -> None:
    result = extract("Дисплейный модуль Apple iPhone 13, оригинал", dicts)
    assert result.matched["part_type_code"] == "display"
    assert result.matched["device_model_key"] == "apple-iphone-13"
    assert result.matched["quality_tier_code"] == "original"
    assert result.matched["device"] in dicts.device_by_alias


def test_typo_falls_back_to_fuzzy_and_lowers_confidence(dicts: Dictionaries) -> None:
    clean = extract("Дисплей для iPhone 14 копия", dicts)
    typo = extract("Диспелй для iPhone 14 копия", dicts)
    assert typo.part_type_id == clean.part_type_id
    assert typo.matched["fuzzy"] == "part_type"
    assert typo.confidence < clean.confidence


def test_confidence_scale(dicts: Dictionaries) -> None:
    full = extract("Задняя крышка чёрная iPhone 13 оригинал", dicts)
    assert full.confidence == pytest.approx(1.0)

    no_color = extract("Задняя крышка iPhone 13 оригинал", dicts)
    assert no_color.confidence == pytest.approx(0.95)

    no_quality = extract("Задняя крышка iPhone 13", dicts)
    assert no_quality.confidence == pytest.approx(0.8)

    no_device = extract("Задняя крышка оригинал", dicts)
    assert no_device.confidence == pytest.approx(0.225)

    assert extract("", dicts).confidence == 0.0


def test_empty_and_noise_titles(dicts: Dictionaries) -> None:
    empty = extract("   ", dicts)
    assert empty.device_id is None
    assert empty.part_type_id is None
    assert empty.matched == {}

    noise = extract("Товар распродажа 12345", dicts)
    assert noise.device_id is None


def test_extract_is_pure(dicts: Dictionaries) -> None:
    title = "Дисплей Apple iPhone 13 в сборе с тачскрином (Original)"
    first = extract(title, dicts)
    second = extract(title, dicts)
    assert first == second


def _fixture_titles() -> list[str]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return [offer["title"] for offer in payload]


REAL_CASES = [
    ("Стекло для переклейки iPhone 11 копия", ("apple-iphone-11", "glass", "copy")),
    (
        "Дисплейный модуль Xiaomi Redmi Note 11, аналог",
        ("xiaomi-redmi-note-11", "display", "copy"),
    ),
    (
        "Шлейф системного разъёма Samsung Galaxy A12 (SM-A125), аналог",
        ("samsung-galaxy-a12", "charging_port", "copy"),
    ),
    (
        "БАТАРЕЯ ХУАВЕЙ П30 ЛАЙТ (HB396286ECW) копия",
        ("huawei-p30-lite", "battery", "copy"),
    ),
    ("Дисплей для Айфон 13 оriginal (OLED)", ("apple-iphone-13", "display", "original")),
    ("Akkumulyator iPhone 13 ORIG", ("apple-iphone-13", "battery", "original")),
    (
        "Акумулятор Ксиоми Редми Ноут 12 копия",
        ("xiaomi-redmi-note-12", "battery", "copy"),
    ),
    ("Системная плата iPhone 13 (Service Pack, без NAND)", ("apple-iphone-13", "board", "service")),
    ("Дисплей  Samsung Galaxy A52 (SM-A525) — копия", ("samsung-galaxy-a52", "display", "copy")),
    ("Дисплейный модуль Apple iPhone 13, OEM премиум", ("apple-iphone-13", "display", "oem_hq")),
    ("экран айфон 13 в сборе ориг", ("apple-iphone-13", "display", "original")),
    ("Нижний шлейф зарядки Поко X3 копия", ("xiaomi-poco-x3", "charging_port", "copy")),
]


@pytest.mark.parametrize(("title", "expected"), REAL_CASES)
def test_extract_real_fixture_titles(title: str, expected: tuple, dicts: Dictionaries) -> None:
    assert title in _fixture_titles()
    assert _codes(title, dicts)[:3] == expected


def test_extraction_coverage_on_demo_fixture(dicts: Dictionaries) -> None:
    titles = _fixture_titles()
    assert len(titles) == 308

    unknown_ids = {
        tier_id for tier_id, code in dicts.quality_code.items() if code == UNKNOWN_QUALITY_CODE
    }
    both = 0
    part_type_hits = 0
    quality_hits = 0
    for title in titles:
        result = extract(title, dicts)
        if result.part_type_id is not None:
            part_type_hits += 1
        if result.device_id is not None and result.part_type_id is not None:
            both += 1
        if result.quality_tier_id is not None and result.quality_tier_id not in unknown_ids:
            quality_hits += 1

    assert both == len(titles)
    assert part_type_hits == len(titles)
    assert quality_hits == len(titles)


def test_every_fixture_title_resolves_to_a_device(dicts: Dictionaries) -> None:
    missing = [title for title in _fixture_titles() if extract(title, dicts).device_id is None]
    assert missing == []
