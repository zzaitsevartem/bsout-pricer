from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.modules.products.schema.product import (
    PriceHistoryResponse,
    ProductListResponse,
    ProductResponse,
)
from src.modules.products.service.product_service import ProductService
from src.modules.shared.deps import get_optional_user, has_active_subscription
from src.modules.stores.service.store_service import StoreService

router = APIRouter(prefix="/api/products", tags=["products"])

PREVIEW_LIMIT = 3


@router.get("", response_model=ProductListResponse)
async def search_products(
    q: str = Query(default="", max_length=500),
    store: str | None = Query(default=None),
    category: str | None = Query(default=None),
    min_price: float | None = Query(default=None),
    max_price: float | None = Query(default=None),
    in_stock: bool | None = Query(default=None),
    sort_by: str = Query(default="price_asc"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
):
    has_sub = await has_active_subscription(db, user)

    # Non-subscribers: force page=1 and cap per_page at PREVIEW_LIMIT
    if not has_sub:
        page = 1
        if per_page > PREVIEW_LIMIT:
            per_page = PREVIEW_LIMIT

    products, total = await ProductService.search(
        db=db,
        query=q,
        store_slug=store,
        category_slug=category,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
    )

    cheapest_price = None
    if products:
        cheapest_price = min(p.price for p in products)

    results = []
    for p in products:
        store_obj = await StoreService.get_by_id(db, p.store_id)
        store_ref = None
        if store_obj:
            store_ref = {"id": store_obj.id, "name": store_obj.name, "slug": store_obj.slug}

        results.append(ProductResponse(
            id=p.id,
            store_id=p.store_id,
            category_id=p.category_id,
            external_id=p.external_id,
            name=p.name,
            description=p.description,
            image_url=p.image_url,
            price=p.price,
            old_price=p.old_price,
            currency=p.currency,
            in_stock=p.in_stock,
            product_url=p.product_url,
            last_updated=p.last_updated,
            is_cheapest=cheapest_price is not None and p.price == cheapest_price,
            store=store_ref,
        ))

    return ProductListResponse(results=results, total=total, page=page, per_page=per_page)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
):
    product = await ProductService.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    store_obj = await StoreService.get_by_id(db, product.store_id)
    store_ref = None
    if store_obj:
        store_ref = {"id": store_obj.id, "name": store_obj.name, "slug": store_obj.slug}

    return ProductResponse(
        id=product.id,
        store_id=product.store_id,
        category_id=product.category_id,
        external_id=product.external_id,
        name=product.name,
        description=product.description,
        image_url=product.image_url,
        price=product.price,
        old_price=product.old_price,
        currency=product.currency,
        in_stock=product.in_stock,
        product_url=product.product_url,
        last_updated=product.last_updated,
        is_cheapest=False,
        store=store_ref,
    )


@router.get("/{product_id}/price-history", response_model=list[PriceHistoryResponse])
async def get_price_history(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_optional_user),
):
    product = await ProductService.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    has_sub = await has_active_subscription(db, user)
    if not has_sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required for price history",
        )

    return await ProductService.get_price_history(db, product_id)
