from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.middleware.subscription_guard import require_feature
from src.modules.auth.model.user import User
from src.modules.export.schema.export import (
    MAX_EXPORT_ROWS,
    MAX_PDF_ROWS,
    ExportLimitExceededDetail,
    ExportUnavailableDetail,
    export_limit_exceeded_detail,
    pdf_unavailable_detail,
)
from src.modules.export.service.csv_writer import (
    CSV_MEDIA_TYPE,
    content_disposition,
    export_filename,
    stream_csv,
)
from src.modules.export.service.export_service import (
    CATALOG_HEADER,
    TRACKING_HEADER,
    ExportService,
)
from src.modules.export.service.pdf import (
    PdfUnavailableError,
    ensure_pdf_available,
    render_table_pdf,
)
from src.modules.shared import get_current_user

router = APIRouter(
    prefix="/api/export",
    tags=["export"],
    dependencies=[Depends(require_feature("export_reports"))],
)

PDF_MEDIA_TYPE = "application/pdf"
CATALOG_PDF_TITLE = "BScout — сравнение цен на запчасти"

LIMIT_RESPONSES = {status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {"model": ExportLimitExceededDetail}}
PDF_RESPONSES = {
    **LIMIT_RESPONSES,
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ExportUnavailableDetail},
}


def _enforce_limit(total: int, limit: int, max_limit: int) -> None:
    if total > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=export_limit_exceeded_detail(limit, total, max_limit),
        )


@router.get("/catalog.csv", responses=LIMIT_RESPONSES)
async def export_catalog_csv(
    q: str = Query(default="", max_length=500),
    device_id: int | None = Query(default=None, ge=1),
    part_type_id: int | None = Query(default=None, ge=1),
    quality_tier_id: int | None = Query(default=None, ge=1),
    sort_by: str = Query(default="min_price_asc"),
    limit: int = Query(default=MAX_EXPORT_ROWS, ge=1, le=MAX_EXPORT_ROWS),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = await ExportService.catalog_total(
        db=db,
        query=q,
        device_id=device_id,
        part_type_id=part_type_id,
        quality_tier_id=quality_tier_id,
    )
    _enforce_limit(total, limit, MAX_EXPORT_ROWS)

    rows = ExportService.iter_catalog_rows(
        db=db,
        limit=limit,
        query=q,
        device_id=device_id,
        part_type_id=part_type_id,
        quality_tier_id=quality_tier_id,
        sort_by=sort_by,
    )
    return StreamingResponse(
        stream_csv(CATALOG_HEADER, rows),
        media_type=CSV_MEDIA_TYPE,
        headers={
            "Content-Disposition": content_disposition(export_filename("catalog", "csv")),
            "X-Export-Rows": str(total),
        },
    )


@router.get("/tracking.csv", responses=LIMIT_RESPONSES)
async def export_tracking_csv(
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=MAX_EXPORT_ROWS, ge=1, le=MAX_EXPORT_ROWS),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = await ExportService.tracking_total(db=db, user_id=current_user.id, is_active=is_active)
    _enforce_limit(total, limit, MAX_EXPORT_ROWS)

    rows = ExportService.iter_tracking_rows(
        db=db,
        user_id=current_user.id,
        limit=limit,
        is_active=is_active,
    )
    return StreamingResponse(
        stream_csv(TRACKING_HEADER, rows),
        media_type=CSV_MEDIA_TYPE,
        headers={
            "Content-Disposition": content_disposition(export_filename("tracking", "csv")),
            "X-Export-Rows": str(total),
        },
    )


@router.get("/catalog.pdf", responses=PDF_RESPONSES)
async def export_catalog_pdf(
    q: str = Query(default="", max_length=500),
    device_id: int | None = Query(default=None, ge=1),
    part_type_id: int | None = Query(default=None, ge=1),
    quality_tier_id: int | None = Query(default=None, ge=1),
    sort_by: str = Query(default="min_price_asc"),
    limit: int = Query(default=MAX_PDF_ROWS, ge=1, le=MAX_PDF_ROWS),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        ensure_pdf_available()
    except PdfUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=pdf_unavailable_detail(str(exc)),
        ) from exc

    total = await ExportService.catalog_total(
        db=db,
        query=q,
        device_id=device_id,
        part_type_id=part_type_id,
        quality_tier_id=quality_tier_id,
    )
    _enforce_limit(total, limit, MAX_PDF_ROWS)

    rows = await ExportService.collect_catalog_rows(
        db=db,
        limit=limit,
        query=q,
        device_id=device_id,
        part_type_id=part_type_id,
        quality_tier_id=quality_tier_id,
        sort_by=sort_by,
    )
    content = render_table_pdf(CATALOG_PDF_TITLE, CATALOG_HEADER, rows)
    return Response(
        content=content,
        media_type=PDF_MEDIA_TYPE,
        headers={
            "Content-Disposition": content_disposition(export_filename("catalog", "pdf")),
            "X-Export-Rows": str(total),
        },
    )
