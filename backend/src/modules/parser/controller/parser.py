from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.parser.schema.parser import ParserRunRequest, ParserStatusResponse
from src.modules.parser.service.exceptions import ParserError
from src.modules.parser.service.parser_service import parser_service
from src.modules.shared import get_current_admin

router = APIRouter(prefix="/api/admin/parsers", tags=["admin"])


@router.get("", response_model=list[ParserStatusResponse])
async def list_parsers(admin=Depends(get_current_admin)):
    return await parser_service.get_statuses()


@router.post("/run", response_model=dict)
async def run_parser(
    body: ParserRunRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    if parser_service.get(body.store_slug) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parser for '{body.store_slug}' not found",
        )

    try:
        return await parser_service.run_one(
            db, body.store_slug, full_sync=body.full_sync, limit=body.limit
        )
    except ParserError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
