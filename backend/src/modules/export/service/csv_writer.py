import csv
import io
import re
from collections.abc import AsyncIterator, Iterable
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

CSV_DELIMITER = ";"
CSV_LINE_TERMINATOR = "\r\n"
CSV_ENCODING = "utf-8"
CSV_MEDIA_TYPE = "text/csv; charset=utf-8"
BOM = "\ufeff"
DECIMAL_SEPARATOR = ","
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
FORMULA_ESCAPE = "'"
CHUNK_ROWS = 200
CENTS = Decimal("0.01")

_NUMERIC = re.compile(r"^-?\d+(?:,\d+)?$")


def escape_formula(value: str) -> str:
    if not value:
        return value
    if _NUMERIC.match(value):
        return value
    if value[0] in FORMULA_PREFIXES:
        return FORMULA_ESCAPE + value
    return value


def text_cell(value) -> str:
    if value is None:
        return ""
    return str(value)


def money_cell(value) -> str:
    if value is None:
        return ""
    quantized = Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)
    return f"{quantized}".replace(".", DECIMAL_SEPARATOR)


def number_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}".replace(".", DECIMAL_SEPARATOR)
    return str(value).replace(".", DECIMAL_SEPARATOR)


def int_cell(value) -> str:
    return str(int(value or 0))


def bool_cell(value) -> str:
    return "да" if value else "нет"


def datetime_cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return str(value)


def join_cell(values: Iterable) -> str:
    return ", ".join(str(item) for item in values if item)


def _writer(buffer: io.StringIO):
    return csv.writer(
        buffer,
        delimiter=CSV_DELIMITER,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator=CSV_LINE_TERMINATOR,
    )


async def stream_csv(
    header: list[str],
    rows: AsyncIterator[list[str]],
    chunk_rows: int = CHUNK_ROWS,
) -> AsyncIterator[bytes]:
    yield BOM.encode(CSV_ENCODING)

    buffer = io.StringIO()
    writer = _writer(buffer)
    writer.writerow([escape_formula(cell) for cell in header])

    pending = 0
    async for row in rows:
        writer.writerow([escape_formula(cell) for cell in row])
        pending += 1
        if pending >= chunk_rows:
            yield buffer.getvalue().encode(CSV_ENCODING)
            buffer.seek(0)
            buffer.truncate(0)
            pending = 0

    tail = buffer.getvalue()
    if tail:
        yield tail.encode(CSV_ENCODING)


def export_filename(kind: str, extension: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"bscout-{kind}-{stamp}.{extension}"


def content_disposition(filename: str) -> str:
    return f'attachment; filename="{filename}"'
