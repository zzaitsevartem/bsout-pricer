from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.shared import get_current_user
from src.modules.tracking.schema.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from src.modules.tracking.service.alert_service import AlertService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    results, total = await AlertService.list_notifications(
        db, user.id, unread=unread, page=page, per_page=per_page
    )
    return NotificationListResponse(results=results, total=total, page=page, per_page=per_page)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return UnreadCountResponse(unread_count=await AlertService.unread_count(db, user.id))


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    notification = await AlertService.mark_read(db, user.id, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification


notifications_router = router
