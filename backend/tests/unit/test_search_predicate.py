import pytest
from sqlalchemy import column
from sqlalchemy.dialects import postgresql

from src.modules.products.service.search_predicate import search_predicate, search_terms

pytestmark = pytest.mark.unit


def test_aliases_and_layout_are_advanced_only():
    assert search_terms("экран", False) == [["экран"]]
    assert "дисплей" in search_terms("dsiplay", True)[0]
    assert "дисплей" in search_terms("lb cgktq".replace(" ", ""), True)[0]
    assert "iphone" in search_terms("шзрщту", True)[0]
    assert "дисплей" in search_terms("dsplay", True)[0]
    assert "samsung" in search_terms("самсунк", True)[0]
    assert "s22" in search_terms("С22", True)[0]


def test_predicate_fuzzy_is_per_word_and_never_changes_model_digits():
    compiled = search_predicate(column("title"), "Nokia a53 13", True).compile(
        dialect=postgresql.dialect()
    )
    sql = str(compiled)
    assert sql.count("strict_word_similarity(") == 3
    assert "AND" in sql and " OR " in sql
    values = list(compiled.params.values())
    assert any("a[[:space:]-]*53" in str(value) for value in values)
    assert any("(^|[^0-9])13" in str(value) for value in values)
    assert "%nokia%" in values
    assert "strict_word_similarity" not in str(search_predicate(column("title"), "Nokai", False))
