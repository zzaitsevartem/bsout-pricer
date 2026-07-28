from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.admin.schema.admin import AdminStatsResponse, UserBriefResponse
from src.modules.admin.schema.moderation import (
    CandidateDecisionResponse,
    MatchCandidateListResponse,
    OfferLinkRequest,
    OfferLinkResponse,
    ReviewOfferListResponse,
)
from src.modules.admin.schema.offer_import import OfferImportItem, OfferImportResponse
from src.modules.admin.service.admin_service import AdminService
from src.modules.admin.service.moderation_service import ModerationError, ModerationService
from src.modules.admin.service.offer_import_service import OfferImportService
from src.modules.shared import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

OFFER_IMPORT_OPENAPI = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"type": "array", "items": OfferImportItem.model_json_schema()}
            }
        },
    }
}


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
async def get_user(
    user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)
):
    user = await AdminService.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/users/{user_id}/toggle-active", response_model=UserBriefResponse)
async def toggle_user_active(
    user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)
):
    user = await AdminService.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await AdminService.toggle_user_active(db, user)


@router.post(
    "/offers/import", response_model=OfferImportResponse, openapi_extra=OFFER_IMPORT_OPENAPI
)
async def import_offers(
    rows: list[Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return await OfferImportService.import_offers(db, rows)


@router.get("/match-candidates", response_model=MatchCandidateListResponse)
async def list_match_candidates(
    status_filter: str = Query(
        default="pending", alias="status", pattern="^(pending|approved|rejected|all)$"
    ),
    offer_id: int | None = Query(default=None, ge=1),
    product_id: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    results, total = await ModerationService.list_candidates(
        db,
        status=status_filter,
        offer_id=offer_id,
        product_id=product_id,
        page=page,
        per_page=per_page,
    )
    return MatchCandidateListResponse(results=results, total=total, page=page, per_page=per_page)


@router.get("/review-offers", response_model=ReviewOfferListResponse)
async def list_review_offers(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    results, total = await ModerationService.list_review_offers(db, page=page, per_page=per_page)
    return ReviewOfferListResponse(results=results, total=total, page=page, per_page=per_page)


@router.post("/match-candidates/{candidate_id}/approve", response_model=CandidateDecisionResponse)
async def approve_match_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    try:
        return await ModerationService.approve(db, candidate_id, admin.id)
    except ModerationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/match-candidates/{candidate_id}/reject", response_model=CandidateDecisionResponse)
async def reject_match_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    try:
        return await ModerationService.reject(db, candidate_id, admin.id)
    except ModerationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/offers/{offer_id}/link", response_model=OfferLinkResponse)
async def link_offer(
    offer_id: int,
    payload: OfferLinkRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    try:
        return await ModerationService.link_offer(db, offer_id, payload.product_id, admin.id)
    except ModerationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/offers/{offer_id}/unlink", response_model=OfferLinkResponse)
async def unlink_offer(
    offer_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    try:
        return await ModerationService.unlink_offer(db, offer_id, admin.id)
    except ModerationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
