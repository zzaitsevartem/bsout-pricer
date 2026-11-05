from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.modules.products.service.comparison_service import (
    ComparisonService,
    _suggestion_display_name,
)


@pytest.mark.parametrize(
    ("canonical", "device", "brand", "expected"),
    [
        (
            "Дисплей Samsung Galaxy A53 OLED",
            "Galaxy A53",
            "Samsung",
            "Samsung Galaxy A53 Дисплей OLED",
        ),
        ("Дисплей iPhone 13 черный", "iPhone 13", "Apple", "iPhone 13 Дисплей черный"),
        ("Крышка NOKIA 5700 оригинал", "Nokia 5700", "Nokia", "NOKIA 5700 Крышка оригинал"),
        (
            "Дисплей Samsung Galaxy A53",
            "Galaxy S22",
            "Samsung",
            "Samsung Galaxy S22 Дисплей Samsung Galaxy A53",
        ),
        (
            "Дисплей Samsung Galaxy A530",
            "Galaxy A53",
            "Samsung",
            "Samsung Galaxy A53 Дисплей Samsung Galaxy A530",
        ),
        ("Дисплей iPhone 130", "iPhone 13", "Apple", "Apple iPhone 13 Дисплей iPhone 130"),
        ("Дисплей айфон13 OLED", "iPhone 13", "Apple", "Apple iPhone 13 Дисплей айфон13 OLED"),
        (
            "Дисплей (Samsung Galaxy A53), OLED",
            "Galaxy A53",
            "Samsung",
            "Samsung Galaxy A53 Дисплей, OLED",
        ),
        (
            "Дисплей Samsung Galaxy A53 (Оригинал, черный)",
            "Galaxy A53",
            "Samsung",
            "Samsung Galaxy A53 Дисплей (Оригинал, черный)",
        ),
        (
            "Аккумулятор Xiaomi Redmi Note 10 Pro усиленный",
            "Redmi Note 10 Pro",
            "Xiaomi",
            "Xiaomi Redmi Note 10 Pro Аккумулятор усиленный",
        ),
        ("Универсальный дисплей", None, None, "Универсальный дисплей"),
        ("iPhone 13 Дисплей", "iPhone 13", "Apple", "iPhone 13 Дисплей"),
    ],
)
def test_suggestion_display_name(canonical, device, brand, expected):
    assert _suggestion_display_name(canonical, device, brand) == expected


async def test_suggestions_use_structured_device_and_brand_and_preserve_canonical():
    rows = [
        SimpleNamespace(
            id=1,
            canonical_name="Дисплей Samsung Galaxy A53 OLED",
            device_name="Galaxy A53",
            brand_name="Samsung",
        ),
        SimpleNamespace(
            id=2, canonical_name="Универсальный дисплей", device_name=None, brand_name=None
        ),
    ]
    db = SimpleNamespace(execute=AsyncMock(return_value=Mock(all=Mock(return_value=rows))))

    result = await ComparisonService.suggestions(db, "дисплей")

    assert result == [
        {
            "id": 1,
            "canonical_name": "Дисплей Samsung Galaxy A53 OLED",
            "display_name": "Samsung Galaxy A53 Дисплей OLED",
        },
        {
            "id": 2,
            "canonical_name": "Универсальный дисплей",
            "display_name": "Универсальный дисплей",
        },
    ]
    sql = str(db.execute.await_args.args[0])
    assert "LEFT OUTER JOIN devices" in sql
    assert "LEFT OUTER JOIN brands" in sql
    assert "devices.brand_id" in sql
