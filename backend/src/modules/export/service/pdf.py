import importlib.util
import io
from datetime import datetime, timezone
from pathlib import Path

FONT_NAME = "DejaVuSans"
FONT_FILENAME = "DejaVuSans.ttf"

FONT_SEARCH_DIRS = (
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "/usr/share/fonts/TTF",
    "/usr/local/share/fonts",
    "/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
)

LIBRARY_MISSING_MESSAGE = (
    "Экспорт в PDF временно недоступен: на сервере не установлена библиотека reportlab. "
    "Воспользуйтесь выгрузкой в CSV."
)

FONT_MISSING_MESSAGE = (
    "Экспорт в PDF временно недоступен: на сервере не найден шрифт DejaVuSans "
    "с поддержкой кириллицы. Воспользуйтесь выгрузкой в CSV."
)

MAX_COLUMN_CHARS = 60


class PdfUnavailableError(RuntimeError):
    pass


def is_reportlab_available() -> bool:
    return importlib.util.find_spec("reportlab") is not None


def find_cyrillic_font() -> str | None:
    for directory in FONT_SEARCH_DIRS:
        candidate = Path(directory) / FONT_FILENAME
        if candidate.is_file():
            return str(candidate)
    return None


def ensure_pdf_available() -> None:
    if not is_reportlab_available():
        raise PdfUnavailableError(LIBRARY_MISSING_MESSAGE)
    if find_cyrillic_font() is None:
        raise PdfUnavailableError(FONT_MISSING_MESSAGE)


def _truncate(value: str) -> str:
    if len(value) <= MAX_COLUMN_CHARS:
        return value
    return value[: MAX_COLUMN_CHARS - 1] + "…"


def render_table_pdf(title: str, header: list[str], rows: list[list[str]]) -> bytes:
    ensure_pdf_available()

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, find_cyrillic_font()))

    title_style = ParagraphStyle(
        name="BScoutTitle",
        fontName=FONT_NAME,
        fontSize=14,
        leading=18,
        alignment=TA_LEFT,
    )
    meta_style = ParagraphStyle(
        name="BScoutMeta",
        fontName=FONT_NAME,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6F6C90"),
        alignment=TA_LEFT,
    )

    generated_at = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=title,
    )

    table_data = [list(header)] + [[_truncate(cell) for cell in row] for row in rows]
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("LEADING", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#010D3E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9D8E4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5FA")]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    story = [
        Paragraph(title, title_style),
        Paragraph(f"BScout · сформировано {generated_at} · строк: {len(rows)}", meta_style),
        Spacer(1, 6 * mm),
        table,
    ]
    doc.build(story)
    return buffer.getvalue()
