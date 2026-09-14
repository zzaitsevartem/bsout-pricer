import pytest

from src.modules.catalog.service.normalizer import (
    edit_distance,
    latin_key,
    normalize,
    stem,
    strip_stopwords,
    token_variants,
    tokenize,
)

pytestmark = pytest.mark.unit


NORMALIZE_CASES = [
    ("", ""),
    ("   ", ""),
    ("Дисплей", "дисплей"),
    ("ДИСПЛЕЙ  Айфон", "дисплей айфон"),
    ("Аккумулятор\tHonor  50", "аккумулятор honor 50"),
    ("Ёмкость и Ёж", "емкость и еж"),
    ("Дисплей, для (iPhone 13) — копия!", "дисплей для iphone 13 копия"),
    ("Шлейф зар-ки айфон 11", "шлейф зар ки айфон 11"),
    ("Камера Айфон 13 осн. оригинал", "камера айфон 13 осн оригинал"),
    ("SM-A125", "sm a125"),
    ("iPhone14", "iphone 14"),
    ("iPhone13 + Touch", "iphone 13 touch"),
    ("Redmi Note12", "redmi note 12"),
    ("Redmi Note 12", "redmi note 12"),
    ("Glass Redmi Note11 (OCA) Copy AAA", "glass redmi note 11 oca copy aaa"),
    ("ip13", "ip13"),
    ("ip13 pro max", "ip13 pro max"),
    ("Poco X3", "poco x3"),
    ("Redmi 9A", "redmi 9a"),
    ("Honor 8X", "honor 8x"),
]


@pytest.mark.parametrize(("raw", "expected"), NORMALIZE_CASES)
def test_normalize_table(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


def test_normalize_folds_cyrillic_homoglyphs_in_mixed_tokens() -> None:
    assert normalize("Дисплей для Айфон 13 оriginal") == "дисплей для айфон 13 original"
    assert normalize("Дисплей Хонор 8Х в сборе") == "дисплей хонор 8x в сборе"


def test_normalize_keeps_pure_cyrillic_tokens_intact() -> None:
    assert normalize("оем копия для с") == "оем копия для с"


def test_normalize_does_not_split_short_model_prefixes() -> None:
    assert normalize("iPhone 13 SM-G991 nth-nx9") == "iphone 13 sm g991 nth nx9"


def test_tokenize_returns_list() -> None:
    assert tokenize("Дисплей для iPhone13, копия") == ["дисплей", "для", "iphone", "13", "копия"]
    assert tokenize("") == []


STEM_CASES = [
    ("крышка", "крышк"),
    ("крышки", "крышк"),
    ("задняя", "задн"),
    ("задние", "задн"),
    ("задней", "задн"),
    ("стекло", "стекл"),
    ("стекла", "стекл"),
    ("тачскрином", "тачскрин"),
    ("системного", "системн"),
    ("системный", "системн"),
    ("основная", "основн"),
    ("дисплея", "диспл"),
    ("дисплей", "диспл"),
    ("дисплейный", "дисплейн"),
    ("батарея", "батар"),
    ("батареи", "батар"),
    ("копия", "коп"),
    ("копии", "коп"),
    ("шлейфы", "шлейф"),
    ("для", "для"),
    ("в", "в"),
    ("iphone", "iphone"),
    ("display", "display"),
]


@pytest.mark.parametrize(("raw", "expected"), STEM_CASES)
def test_stem_table(raw: str, expected: str) -> None:
    assert stem(raw) == expected


LATIN_KEY_PAIRS = [
    ("айфон", "iphone"),
    ("лайт", "lite"),
    ("хуавей", "huawei"),
    ("п30", "p30"),
    ("галакси", "galaxy"),
    ("поко", "poco"),
    ("хонор", "honor"),
    ("макс", "max"),
    ("плюс", "plus"),
    ("ультра", "ultra"),
    ("камера", "camera"),
    ("бузер", "buzzer"),
    ("акумулятор", "аккумулятор"),
]


@pytest.mark.parametrize(("cyrillic", "latin"), LATIN_KEY_PAIRS)
def test_latin_key_unifies_scripts(cyrillic: str, latin: str) -> None:
    assert latin_key(cyrillic) == latin_key(latin)


def test_latin_key_keeps_distinct_models_apart() -> None:
    assert latin_key("iphone") != latin_key("redmi")
    assert latin_key("galaxy") != latin_key("poco")
    assert latin_key("copy") != latin_key("original")


def test_latin_key_skips_very_short_tokens() -> None:
    assert latin_key("с") == "с"
    assert latin_key("x3") == "x3"


def test_token_variants_contains_source_stem_and_latin_key() -> None:
    variants = token_variants("крышки")
    assert "крышки" in variants
    assert "крышк" in variants
    assert token_variants("айфон") & token_variants("iphone")


def test_strip_stopwords_removes_plain_and_inflected_forms() -> None:
    stopwords = frozenset({"для", "в", "с", "нов"})
    tokens = ["дисплей", "для", "iphone", "13", "в", "сборе", "с", "нового"]
    assert strip_stopwords(tokens, stopwords) == ["дисплей", "iphone", "13", "сборе"]


def test_strip_stopwords_with_empty_set_is_identity() -> None:
    tokens = ["дисплей", "для"]
    assert strip_stopwords(tokens, frozenset()) == tokens


EDIT_DISTANCE_CASES = [
    ("дисплей", "дисплей", 0),
    ("диспелй", "дисплей", 1),
    ("дисплей", "дисплеи", 1),
    ("дисплей", "дисплй", 1),
    ("дисплей", "камера", 2),
    ("аккумулятор", "камера", 2),
]


@pytest.mark.parametrize(("left", "right", "expected"), EDIT_DISTANCE_CASES)
def test_edit_distance_table(left: str, right: str, expected: int) -> None:
    assert edit_distance(left, right, 1) == expected


def test_edit_distance_respects_limit() -> None:
    assert edit_distance("камера", "камеры", 1) == 1
    assert edit_distance("камера", "батарея", 1) > 1


def test_normalize_is_idempotent() -> None:
    for raw, _ in NORMALIZE_CASES:
        once = normalize(raw)
        assert normalize(once) == once


REAL_TITLES = [
    "Стекло для переклейки iPhone 11 копия",
    "Дисплейный модуль Xiaomi Redmi Note 11, аналог",
    "Main camera iPhone14 OEM",
    "Шлейф системного разъёма Samsung Galaxy A12 (SM-A125), аналог",
    "БАТАРЕЯ ХУАВЕЙ П30 ЛАЙТ (HB396286ECW) копия",
    "Дисплей  Samsung Galaxy A52 (SM-A525) — копия",
    "S23 Galaxy Samsung дисплей ORIG (OLED)",
]


@pytest.mark.parametrize("title", REAL_TITLES)
def test_normalize_real_titles_produce_clean_tokens(title: str) -> None:
    tokens = tokenize(title)
    assert tokens
    assert all(token.isalnum() for token in tokens)
    assert all(token == token.lower() for token in tokens)
    assert "ё" not in " ".join(tokens)


def test_normalize_real_title_exact() -> None:
    assert (
        normalize("Шлейф системного разъёма Samsung Galaxy A12 (SM-A125), аналог")
        == "шлейф системного разъема samsung galaxy a12 sm a125 аналог"
    )
    assert normalize("БАТАРЕЯ ХУАВЕЙ П30 ЛАЙТ (HB396286ECW) копия") == (
        "батарея хуавей п30 лайт hb396286 ecw копия"
    )
