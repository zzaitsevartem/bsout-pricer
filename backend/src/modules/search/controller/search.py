from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.auth.model.user import User
from src.modules.search.schema.search_history import SearchHistoryResponse
from src.modules.search.service.search_history_service import SearchHistoryService
from src.modules.shared import get_current_user

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/history", response_model=list[SearchHistoryResponse])
async def get_search_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await SearchHistoryService.get_by_user(db, current_user.id)
