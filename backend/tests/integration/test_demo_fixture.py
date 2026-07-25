import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "demo_offers.json"

ALLOWED_STORES = {"tgsm", "profi", "liberti", "greenspark", "divizion"}
ALLOWED_STOCK_STATUSES = {"in_stock", "low", "out", "preorder", "unknown"}

REQUIRED_FIELDS = {
    "store_slug",
    "source_sku",
    "title",
    "price_retail",
    "price_opt",
    "price_old",
    "stock_status",
    "stock_qty",
    "url",
    "image_url",
    "description",
    "category",
}

STORE_URL_HOST = {
    "tgsm": "https://taggsm.ru/",
    "profi": "https://siriust.ru/",
    "liberti": "https://liberti.ru/",
    "greenspark": "https://green-spark.ru/",
    "divizion": "https://divizion126.ru/",
}

DEVICE_ALIASES = [
    ("iphone_15", ("iphone 15", "iphone15", "айфон 15")),
    ("iphone_14", ("iphone 14", "iphone14", "айфон 14")),
    ("iphone_13", ("iphone 13", "iphone13", "айфон 13")),
    ("iphone_12", ("iphone 12", "iphone12", "айфон 12")),
    ("iphone_11", ("iphone 11", "iphone11", "айфон 11")),
    ("galaxy_s23", ("galaxy s23", "s23", "sm-s911")),
    ("galaxy_s21", ("galaxy s21", "s21", "sm-g991")),
    ("galaxy_a52", ("galaxy a52", "a52", "sm-a525")),
    ("galaxy_a12", ("galaxy a12", "a12", "sm-a125")),
    ("redmi_note_12", ("redmi note 12", "redmi note12", "редми ноут 12", "note 12")),
    ("redmi_note_11", ("redmi note 11", "redmi note11", "редми ноут 11", "note 11")),
    ("poco_x3", ("poco x3", "поко x3")),
    ("p30_lite", ("p30 lite", "п30 лайт")),
    ("p40_lite", ("p40 lite", "п40 лайт")),
    ("honor_8x", ("honor 8x", "хонор 8x", "хонор 8х")),
    ("honor_50", ("honor 50", "хонор 50")),
]

PART_ALIASES = [
    ("back_cover", ("задняя крышка", "крышка", "крышки", "back cover")),
    ("glass", ("стекло", "glass")),
    (
        "charging_port",
        (
            "шлейф зарядки",
            "шлейф зар",
            "шлейф системного",
            "разъём зарядки",
            "разъем зарядки",
            "charging port",
        ),
    ),
    ("display", ("дисплей", "диспелй", "экран", "lcd", "display")),
    ("battery", ("аккумулятор", "акумулятор", "акб", "батаре", "battery", "akkumulyator")),
    ("camera", ("камера", "camera")),
    ("speaker", ("динамик", "buzzer", "бузер")),
    ("board", ("плата", "motherboard", "board")),
]

TIER_ALIASES = [
    ("service", ("service", "сервисн")),
    ("oem_hq", ("oem", "оем", "премиум")),
    ("copy", ("копия", "копии", "аналог", "copy")),
    ("original", ("оригинал", "original", "оriginal", "ориг", "orig")),
]

MIN_RECORDS = 250
MAX_RECORDS = 400
MIN_MULTI_STORE_GROUPS = 20


def _load() -> list[dict]:
    with FIXTURE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def offers() -> list[dict]:
    return _load()


def _match(haystack: str, aliases) -> str | None:
    for key, needles in aliases:
        for needle in needles:
            if needle in haystack:
                return key
    return None


def _canonical_key(title: str) -> tuple[str | None, str | None, str | None]:
    lowered = title.lower().replace("ё", "е")
    return (
        _match(lowered, DEVICE_ALIASES),
        _match(lowered, PART_ALIASES),
        _match(lowered, TIER_ALIASES),
    )


def test_fixture_file_exists():
    assert FIXTURE_PATH.is_file()


def test_fixture_is_valid_json_array(offers):
    assert isinstance(offers, list)
    assert MIN_RECORDS <= len(offers) <= MAX_RECORDS
    assert all(isinstance(item, dict) for item in offers)


def test_every_record_has_exact_field_set(offers):
    for offer in offers:
        assert set(offer) == REQUIRED_FIELDS, offer.get("source_sku")


def test_store_slugs_are_allowed_and_all_present(offers):
    slugs = {offer["store_slug"] for offer in offers}
    assert slugs == ALLOWED_STORES


def test_source_sku_is_unique_per_store(offers):
    seen = Counter((offer["store_slug"], offer["source_sku"]) for offer in offers)
    duplicates = [key for key, count in seen.items() if count > 1]
    assert duplicates == []


def test_titles_are_non_empty_and_reasonable(offers):
    for offer in offers:
        title = offer["title"]
        assert isinstance(title, str)
        assert 8 <= len(title.strip()) <= 200, title


def test_prices_are_positive_decimal_strings(offers):
    for offer in offers:
        retail = Decimal(offer["price_retail"])
        assert retail > 0, offer["source_sku"]
        assert offer["price_retail"] == f"{retail:.2f}"
        for field in ("price_opt", "price_old"):
            value = offer[field]
            if value is None:
                continue
            parsed = Decimal(value)
            assert parsed > 0, (offer["source_sku"], field)
            assert value == f"{parsed:.2f}"


def test_price_opt_is_below_retail_when_present(offers):
    with_opt = [offer for offer in offers if offer["price_opt"] is not None]
    assert with_opt
    for offer in with_opt:
        assert Decimal(offer["price_opt"]) < Decimal(offer["price_retail"]), offer["source_sku"]


def test_price_old_is_above_retail_when_present(offers):
    with_old = [offer for offer in offers if offer["price_old"] is not None]
    assert with_old
    for offer in with_old:
        assert Decimal(offer["price_old"]) > Decimal(offer["price_retail"]), offer["source_sku"]


def test_both_null_and_filled_optional_prices_exist(offers):
    assert any(offer["price_opt"] is None for offer in offers)
    assert any(offer["price_opt"] is not None for offer in offers)
    assert any(offer["price_old"] is None for offer in offers)
    assert any(offer["price_old"] is not None for offer in offers)


def test_stock_status_values_are_allowed_and_diverse(offers):
    statuses = Counter(offer["stock_status"] for offer in offers)
    assert set(statuses) <= ALLOWED_STOCK_STATUSES
    for required in ("in_stock", "low", "out", "preorder"):
        assert statuses[required] > 0, required


def test_stock_qty_is_null_or_non_negative_int(offers):
    for offer in offers:
        qty = offer["stock_qty"]
        if qty is None:
            continue
        assert isinstance(qty, int) and not isinstance(qty, bool)
        assert qty >= 0, offer["source_sku"]
    assert any(offer["stock_qty"] is None for offer in offers)
    assert any(offer["stock_qty"] is not None for offer in offers)


def test_urls_point_to_the_declared_store(offers):
    for offer in offers:
        assert offer["url"].startswith(STORE_URL_HOST[offer["store_slug"]]), offer["source_sku"]


def test_optional_text_fields_are_null_or_non_empty(offers):
    for field in ("image_url", "description", "category"):
        values = [offer[field] for offer in offers]
        assert any(value is None for value in values), field
        assert any(value is not None for value in values), field
        for value in values:
            assert value is None or (isinstance(value, str) and value.strip()), field


def test_image_urls_are_absolute_when_present(offers):
    for offer in offers:
        image_url = offer["image_url"]
        assert image_url is None or image_url.startswith("https://"), offer["source_sku"]


def test_every_title_resolves_to_device_part_and_tier(offers):
    unresolved = []
    for offer in offers:
        device, part, tier = _canonical_key(offer["title"])
        if not (device and part and tier):
            unresolved.append((offer["store_slug"], offer["source_sku"], offer["title"]))
    assert unresolved == []


def test_dataset_covers_all_brands_part_types_and_tiers(offers):
    devices = set()
    parts = set()
    tiers = set()
    for offer in offers:
        device, part, tier = _canonical_key(offer["title"])
        devices.add(device)
        parts.add(part)
        tiers.add(tier)
    assert tiers == {"original", "oem_hq", "copy", "service"}
    assert parts == {key for key, _ in PART_ALIASES}
    assert devices == {key for key, _ in DEVICE_ALIASES}


def test_same_position_is_offered_by_at_least_three_stores(offers):
    groups = defaultdict(set)
    for offer in offers:
        groups[_canonical_key(offer["title"])].add(offer["store_slug"])
    multi_store = {key: stores for key, stores in groups.items() if len(stores) >= 3}
    assert len(multi_store) >= MIN_MULTI_STORE_GROUPS
    assert any(len(stores) == len(ALLOWED_STORES) for stores in multi_store.values())


def test_multi_store_positions_have_differing_titles_and_prices(offers):
    grouped = defaultdict(list)
    for offer in offers:
        grouped[_canonical_key(offer["title"])].append(offer)
    checked = 0
    for key, items in grouped.items():
        if len({item["store_slug"] for item in items}) < 3:
            continue
        checked += 1
        titles = {item["title"] for item in items}
        prices = {item["price_retail"] for item in items}
        assert len(titles) == len(items), key
        assert len(prices) > 1, key
    assert checked >= MIN_MULTI_STORE_GROUPS


def test_quality_tiers_stay_separate_for_the_same_device_and_part(offers):
    by_device_part = defaultdict(set)
    for offer in offers:
        device, part, tier = _canonical_key(offer["title"])
        by_device_part[(device, part)].add(tier)
    assert any(len(tiers) >= 3 for tiers in by_device_part.values())
    assert ("iphone_13", "display") in by_device_part
    assert len(by_device_part[("iphone_13", "display")]) == 4


def test_hard_cases_are_present(offers):
    titles = {offer["title"] for offer in offers}
    expected = [
        "экран айфон 13 в сборе ориг",
        "LCD iPhone13 + Touch ORIG",
        "Дисплей для Айфон 13 оriginal (OLED)",
        "Диспелй для iPhone 14 копия",
        "Акумулятор Ксиоми Редми Ноут 12 копия",
        "Дисплей Хонор 8Х в сборе копия",
        "Шлейф зар-ки айфон 11 копия",
        "Akkumulyator iPhone 13 ORIG",
        "Дисплей для SM-G991 (S21) ориг",
        "Крышки задние для iPhone 15 оригинал",
        "БАТАРЕЯ ХУАВЕЙ П30 ЛАЙТ (HB396286ECW) копия",
        "Display iPhone 14 assembly Original",
    ]
    assert [title for title in expected if title not in titles] == []


def test_price_ranges_look_realistic(offers):
    displays = []
    batteries = []
    for offer in offers:
        _, part, _ = _canonical_key(offer["title"])
        price = Decimal(offer["price_retail"])
        if part == "display":
            displays.append(price)
        elif part == "battery":
            batteries.append(price)
    assert displays and batteries
    assert min(displays) >= Decimal("800")
    assert max(displays) <= Decimal("9500")
    assert min(batteries) >= Decimal("600")
    assert max(batteries) <= Decimal("2600")
