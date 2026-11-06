import pytest
from sqlalchemy import column
from sqlalchemy.dialects import postgresql

from src.modules.products.service.search_predicate import search_predicate, search_terms

pytestmark = pytest.mark.unit


def test_layout_transliteration_and_fuzzy_policy():
    assert [row[1] for row in search_terms("ddjlt yf lheujv zpsrt", False)] == [
        "вводе",
        "на",
        "другом",
        "языке",
    ]
    for latin, cyrillic in (
        ("plenka", "пленка"),
        ("shleyf", "шлейф"),
        ("shleif", "шлейф"),
        ("steklo", "стекло"),
        ("iphone", "айфон"),
    ):
        assert cyrillic in search_terms(latin, False)[0]
        assert latin in search_terms(cyrillic, False)[0]
    assert "дисплей" not in search_terms("dsplay", False)[0]
    assert "дисплей" in search_terms("dsplay", True)[0]
    assert "samsung" in search_terms("самсунк", True)[0]
    assert "s22" in search_terms("С22", True)[0]


def test_boundaries_budget_and_sql_operators():
    for token in ("se", "xr", "gt", "pro", "sm-a525", "sku_123"):
        assert all(len(row) == 1 for row in search_terms(token, True))
    terms = search_terms(" ".join(["экран"] * 100), True)
    assert all(row[0] == "экран" and len(row) <= 12 for row in terms)
    assert sum(len(row) - 1 for row in terms) <= 64
    compiled = search_predicate(column("title"), "плёнка iPhone 15 Pro", False).compile(
        dialect=postgresql.dialect()
    )
    assert " AND " in str(compiled) and " OR " in str(compiled)
    assert "пл[её]нка" in compiled.params.values()
    assert any("(^|[^0-9])15" in str(value) for value in compiled.params.values())
    assert "strict_word_similarity" not in str(compiled)
    fuzzy = str(search_predicate(column("title"), "Nokia a53 13", True))
    assert "strict_word_similarity" in fuzzy
