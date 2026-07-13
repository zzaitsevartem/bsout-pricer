from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.admin.schema.admin import AdminStatsResponse, UserBriefResponse
from src.modules.admin.service.admin_service import AdminService
from src.modules.shared import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    return await AdminService.get_stats(db)


@router.get("/users", response_model=list[UserBriefResponse])
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return await AdminService.get_users(db, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UserBriefResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    user = await AdminService.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/users/{user_id}/toggle-active", response_model=UserBriefResponse)
async def toggle_user_active(user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    user = await AdminService.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await AdminService.toggle_user_active(db, user)
