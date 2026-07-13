from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.categories.schema.category import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest
from src.modules.categories.service.category_service import CategoryService
from src.modules.shared import get_current_admin

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    return await CategoryService.get_all(db)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    category = await CategoryService.get_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(body: CategoryCreateRequest, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    existing = await CategoryService.get_by_slug(db, body.slug)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category with this slug already exists")
    return await CategoryService.create(db, name=body.name, slug=body.slug)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, body: CategoryUpdateRequest, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    category = await CategoryService.get_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return await CategoryService.update(db, category, body.model_dump(exclude_none=True))
