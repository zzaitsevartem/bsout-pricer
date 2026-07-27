from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

import src.modules.export.service.pdf as pdf_module
from src.modules.export.schema.export import (
    EXPORT_LIMIT_EXCEEDED_CODE,
    EXPORT_PDF_UNAVAILABLE_CODE,
    MAX_EXPORT_ROWS,
    MAX_PDF_ROWS,
    export_limit_exceeded_detail,
    pdf_unavailable_detail,
)
from src.modules.export.service.csv_writer import (
    BOM,
    CSV_DELIMITER,
    CSV_LINE_TERMINATOR,
    bool_cell,
    content_disposition,
    datetime_cell,
    escape_formula,
    export_filename,
    int_cell,
    join_cell,
    money_cell,
    number_cell,
    stream_csv,
    text_cell,
)
from src.modules.export.service.export_service import (
    CATALOG_HEADER,
    TRACKING_HEADER,
    ExportService,
)
from src.modules.export.service.pdf import (
    PdfUnavailableError,
    ensure_pdf_available,
    find_cyrillic_font,
    is_reportlab_available,
)

pytestmark = pytest.mark.unit

_FALLBACK_CYRILLIC_FONT = "/Library/Fonts/Arial Unicode.ttf"


async def _arows(rows):
    for row in rows:
        yield row


@pytest.mark.parametrize("dangerous", ["=", "+", "-", "@", "\t", "\r"])
def test_formula_prefixes_are_escaped(dangerous):
    value = f"{dangerous}cmd|' /C calc'!A0"

    assert escape_formula(value) == "'" + value


def test_plain_text_is_left_untouched():
    assert escape_formula("Дисплей iPhone 13") == "Дисплей iPhone 13"
    assert escape_formula("") == ""


@pytest.mark.parametrize("value", ["1234,50", "-1234,50", "0", "-7"])
def test_numbers_are_not_escaped_even_with_leading_minus(value):
    assert escape_formula(value) == value


def test_money_cell_uses_comma_and_two_decimals():
    assert money_cell(Decimal("1234.5")) == "1234,50"
    assert money_cell(Decimal("-100")) == "-100,00"
    assert money_cell(None) == ""


def test_number_and_int_and_bool_cells():
    assert number_cell(-12.3456) == "-12,35"
    assert number_cell(None) == ""
    assert int_cell(None) == "0"
    assert int_cell(4) == "4"
    assert bool_cell(True) == "да"
    assert bool_cell(False) == "нет"


def test_text_datetime_and_join_cells():
    moment = datetime(2026, 7, 27, 9, 5, tzinfo=timezone.utc)

    assert text_cell(None) == ""
    assert datetime_cell(None) == ""
    assert datetime_cell(moment) == "27.07.2026 09:05"
    assert join_cell(["ТГСМ", None, "Дивизион"]) == "ТГСМ, Дивизион"


async def test_stream_csv_joins_header_cells_with_a_semicolon():
    text = b"".join(
        [chunk async for chunk in stream_csv(["Товар", "Цена"], _arows([["Дисплей", "1200,00"]]))]
    ).decode("utf-8")

    assert text.startswith(BOM)
    assert text.endswith(CSV_LINE_TERMINATOR)
    assert f"Товар{CSV_DELIMITER}Цена" in text
    assert f"Дисплей{CSV_DELIMITER}1200,00" in text


async def test_stream_csv_emits_bom_first_and_decodes_as_utf8():
    chunks = [chunk async for chunk in stream_csv(["Товар"], _arows([["Дисплей"]]))]
    payload = b"".join(chunks)

    assert payload.startswith(b"\xef\xbb\xbf")
    text = payload.decode("utf-8")
    assert text.startswith(BOM)
    assert text[1:] == f"Товар{CSV_LINE_TERMINATOR}Дисплей{CSV_LINE_TERMINATOR}"


async def test_stream_csv_escapes_formulas_in_body():
    rows = _arows([["=SUM(A1:A2)", "-100,00"]])

    payload = b"".join([chunk async for chunk in stream_csv(["a", "b"], rows)])
    text = payload.decode("utf-8")

    assert "'=SUM(A1:A2)" in text
    assert "-100,00" in text
    assert "'-100,00" not in text


async def test_stream_csv_chunks_instead_of_buffering_everything():
    rows = _arows([[str(index)] for index in range(10)])

    chunks = [chunk async for chunk in stream_csv(["n"], rows, chunk_rows=3)]

    assert len(chunks) > 3
    text = b"".join(chunks).decode("utf-8")
    assert text.count(CSV_LINE_TERMINATOR) == 11


async def test_stream_csv_writes_header_even_without_rows():
    payload = b"".join([chunk async for chunk in stream_csv(["Товар"], _arows([]))])

    assert payload.decode("utf-8") == BOM + f"Товар{CSV_LINE_TERMINATOR}"


async def test_stream_csv_quotes_values_containing_the_delimiter():
    rows = _arows([["ТГСМ; Дивизион"]])

    text = b"".join([chunk async for chunk in stream_csv(["Магазины"], rows)]).decode("utf-8")

    assert '"ТГСМ; Дивизион"' in text


def test_catalog_row_matches_header_and_resolves_store_names():
    item = {
        "canonical_name": "Дисплей iPhone 13 копия",
        "brand": {"name": "Apple"},
        "device": {"name": "iPhone 13"},
        "part_type": {"name_ru": "Дисплей"},
        "quality_tier": {"name_ru": "Копия"},
        "min_price_retail": Decimal("5400.00"),
        "min_price_opt": Decimal("4800.00"),
        "stores_count": 2,
        "offers_count": 3,
        "store_slugs": ["tgsm", "unknown-slug"],
    }

    row = ExportService.catalog_row(item, {"tgsm": "ТГСМ"})

    assert len(row) == len(CATALOG_HEADER)
    assert row[0] == "Дисплей iPhone 13 копия"
    assert row[5] == "5400,00"
    assert row[6] == "4800,00"
    assert row[9] == "ТГСМ, unknown-slug"


def test_catalog_row_tolerates_missing_dictionaries():
    row = ExportService.catalog_row({"canonical_name": "Без справочников"}, {})

    assert len(row) == len(CATALOG_HEADER)
    assert row[1:5] == ["", "", "", ""]
    assert row[7] == "0"


def test_tracking_row_matches_header():
    item = {
        "canonical_name": "Аккумулятор iPhone 12",
        "current_price": Decimal("2100.00"),
        "target_price": Decimal("2000.00"),
        "price_delta": Decimal("-150.00"),
        "price_delta_pct": -6.66,
        "stores_count": 3,
        "target_reached": False,
        "is_active": True,
        "created_at": datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
    }

    row = ExportService.tracking_row(item)

    assert len(row) == len(TRACKING_HEADER)
    assert row[3] == "-150,00"
    assert row[4] == "-6,66"
    assert row[6] == "нет"
    assert row[7] == "да"


def test_export_filename_and_content_disposition():
    filename = export_filename("catalog", "csv")

    assert filename.startswith("bscout-catalog-")
    assert filename.endswith(".csv")
    assert content_disposition(filename) == f'attachment; filename="{filename}"'


def test_limit_detail_is_actionable_russian():
    detail = export_limit_exceeded_detail(limit=10, total=42, max_limit=MAX_EXPORT_ROWS)

    assert detail["code"] == EXPORT_LIMIT_EXCEEDED_CODE
    assert detail["limit"] == 10
    assert detail["total"] == 42
    assert detail["max_limit"] == MAX_EXPORT_ROWS
    assert "42" in detail["message"]
    assert "Уточните фильтры" in detail["message"]


def test_pdf_detail_carries_code_and_message():
    detail = pdf_unavailable_detail("нет библиотеки")

    assert detail["code"] == EXPORT_PDF_UNAVAILABLE_CODE
    assert detail["message"] == "нет библиотеки"


def test_pdf_row_cap_is_lower_than_csv_cap():
    assert MAX_PDF_ROWS <= MAX_EXPORT_ROWS


def test_pdf_module_stays_importable_and_reports_availability():
    assert isinstance(is_reportlab_available(), bool)
    assert find_cyrillic_font() is None or isinstance(find_cyrillic_font(), str)


def test_missing_library_raises_actionable_russian_error(monkeypatch):
    monkeypatch.setattr(pdf_module, "is_reportlab_available", lambda: False)

    with pytest.raises(PdfUnavailableError) as exc_info:
        ensure_pdf_available()

    message = str(exc_info.value)
    assert "reportlab" in message
    assert "CSV" in message


def test_missing_font_raises_actionable_russian_error(monkeypatch):
    monkeypatch.setattr(pdf_module, "is_reportlab_available", lambda: True)
    monkeypatch.setattr(pdf_module, "find_cyrillic_font", lambda: None)

    with pytest.raises(PdfUnavailableError) as exc_info:
        ensure_pdf_available()

    message = str(exc_info.value)
    assert "DejaVuSans" in message
    assert "CSV" in message


def test_render_table_pdf_produces_a_pdf_with_a_cyrillic_font(monkeypatch):
    pytest.importorskip("reportlab")

    font = pdf_module.find_cyrillic_font() or _FALLBACK_CYRILLIC_FONT
    if not Path(font).is_file():
        pytest.skip("no Cyrillic TTF available on this host")

    monkeypatch.setattr(pdf_module, "find_cyrillic_font", lambda: font)

    content = pdf_module.render_table_pdf(
        "Отчёт BScout",
        CATALOG_HEADER,
        [
            [
                "Дисплей iPhone 13",
                "Apple",
                "iPhone 13",
                "Дисплей",
                "Копия",
                "5400,00",
                "",
                "1",
                "1",
                "ТГСМ",
            ]
        ],
    )

    assert content.startswith(b"%PDF")
    assert len(content) > 1000
