from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.broadcast.model.broadcast import RecipientStatus
from src.modules.broadcast.schema.broadcast import (
    BroadcastCreateRequest,
    BroadcastListResponse,
    BroadcastPreviewRequest,
    BroadcastPreviewResponse,
    BroadcastRecipientListResponse,
    BroadcastResponse,
    BroadcastSendTestRequest,
    BroadcastSendTestResponse,
)
from src.modules.broadcast.service.broadcast_service import BroadcastError, BroadcastService
from src.modules.shared import get_current_admin

router = APIRouter(prefix="/api/admin/broadcasts", tags=["admin"])


def _http_error(exc: BroadcastError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


async def _load_broadcast(db: AsyncSession, broadcast_id: int, admin_id: int):
    broadcast = await BroadcastService.get(db, broadcast_id)
    if broadcast is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рассылка не найдена")
    return broadcast


@router.get("", response_model=BroadcastListResponse)
async def list_broadcasts(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    items, total = await BroadcastService.paginate(db, page=page, per_page=per_page)
    return BroadcastListResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=BroadcastResponse, status_code=status.HTTP_201_CREATED)
async def create_broadcast(
    payload: BroadcastCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    try:
        broadcast = await BroadcastService.create(db, payload, creator_id=admin.id)
    except BroadcastError as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return broadcast


@router.post("/preview", response_model=BroadcastPreviewResponse)
async def preview_broadcast(
    payload: BroadcastPreviewRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    try:
        return await BroadcastService.preview(db, payload)
    except BroadcastError as exc:
        raise _http_error(exc) from exc


@router.get("/{broadcast_id}", response_model=BroadcastResponse)
async def get_broadcast(
    broadcast_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return await _load_broadcast(db, broadcast_id, admin.id)


@router.get("/{broadcast_id}/recipients", response_model=BroadcastRecipientListResponse)
async def list_broadcast_recipients(
    broadcast_id: int,
    status_filter: RecipientStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    await _load_broadcast(db, broadcast_id, admin.id)
    items, total = await BroadcastService.list_recipients(
        db,
        broadcast_id,
        status_filter=status_filter,
        page=page,
        per_page=per_page,
    )
    return BroadcastRecipientListResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("/{broadcast_id}/send-test", response_model=BroadcastSendTestResponse)
async def send_test_broadcast(
    broadcast_id: int,
    payload: BroadcastSendTestRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    broadcast = await _load_broadcast(db, broadcast_id, admin.id)
    to = payload.email or admin.email
    try:
        sent_to = await BroadcastService.send_test(broadcast, to)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Не удалось отправить тестовое письмо: {exc}",
        ) from exc
    return BroadcastSendTestResponse(sent_to=sent_to)


@router.post("/{broadcast_id}/launch", response_model=BroadcastResponse)
async def launch_broadcast(
    broadcast_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    broadcast = await _load_broadcast(db, broadcast_id, admin.id)
    try:
        launched = await BroadcastService.launch(db, broadcast)
    except BroadcastError as exc:
        raise _http_error(exc) from exc
    return launched


@router.post("/{broadcast_id}/cancel", response_model=BroadcastResponse)
async def cancel_broadcast(
    broadcast_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    broadcast = await _load_broadcast(db, broadcast_id, admin.id)
    try:
        return await BroadcastService.cancel(db, broadcast)
    except BroadcastError as exc:
        raise _http_error(exc) from exc


@router.delete("/{broadcast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_broadcast(
    broadcast_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    broadcast = await _load_broadcast(db, broadcast_id, admin.id)
    try:
        await BroadcastService.delete(db, broadcast)
    except BroadcastError as exc:
        raise _http_error(exc) from exc
    await db.commit()
