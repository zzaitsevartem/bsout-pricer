from pydantic import BaseModel

EXPORT_LIMIT_EXCEEDED_CODE = "export_limit_exceeded"
EXPORT_PDF_UNAVAILABLE_CODE = "export_pdf_unavailable"

MAX_EXPORT_ROWS = 10_000
MAX_PDF_ROWS = 2_000


class ExportLimitExceededDetail(BaseModel):
    code: str
    limit: int
    total: int
    max_limit: int
    message: str


class ExportUnavailableDetail(BaseModel):
    code: str
    message: str


def export_limit_exceeded_detail(limit: int, total: int, max_limit: int) -> dict:
    return {
        "code": EXPORT_LIMIT_EXCEEDED_CODE,
        "limit": limit,
        "total": total,
        "max_limit": max_limit,
        "message": (
            f"Выгрузка содержит {total} строк, а лимит запроса — {limit} "
            f"(максимум {max_limit}). Уточните фильтры, чтобы уменьшить выборку."
        ),
    }


def pdf_unavailable_detail(message: str) -> dict:
    return {
        "code": EXPORT_PDF_UNAVAILABLE_CODE,
        "message": message,
    }
