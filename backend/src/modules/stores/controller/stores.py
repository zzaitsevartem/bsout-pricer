from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.shared import get_current_admin
from src.modules.stores.schema.store import StoreCreateRequest, StoreResponse, StoreUpdateRequest
from src.modules.stores.service.store_service import StoreService

router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.get("", response_model=list[StoreResponse])
async def list_stores(db: AsyncSession = Depends(get_db)):
    return await StoreService.get_all(db)


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(store_id: int, db: AsyncSession = Depends(get_db)):
    store = await StoreService.get_by_id(db, store_id)
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return store


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(body: StoreCreateRequest, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    existing = await StoreService.get_by_slug(db, body.slug)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Store with this slug already exists")
    return await StoreService.create(db, name=body.name, slug=body.slug, website_url=body.website_url, logo_url=body.logo_url)


@router.patch("/{store_id}", response_model=StoreResponse)
async def update_store(store_id: int, body: StoreUpdateRequest, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    store = await StoreService.get_by_id(db, store_id)
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    return await StoreService.update(db, store, body.model_dump(exclude_none=True))
