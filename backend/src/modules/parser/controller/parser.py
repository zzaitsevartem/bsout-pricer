from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.parser.schema.parser import ParserRunRequest, ParserStatusResponse
from src.modules.parser.service.base import parser_manager
from src.modules.shared import get_current_admin

router = APIRouter(prefix="/api/admin/parsers", tags=["admin"])


@router.get("", response_model=list[ParserStatusResponse])
async def list_parsers(admin=Depends(get_current_admin)):
    return parser_manager.get_statuses()


@router.post("/run", response_model=dict)
async def run_parser(body: ParserRunRequest, admin=Depends(get_current_admin)):
    parser = parser_manager.get(body.store_slug)
    if parser is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Parser for '{body.store_slug}' not found")

    parser.reset_errors()
    return {"store_slug": body.store_slug, "status": "triggered", "full_sync": body.full_sync}
