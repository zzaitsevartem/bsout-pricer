from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.middleware.subscription_guard import is_fuzzy_enabled, require_active_subscription
from src.modules.products.schema.comparison import (
    CatalogListResponse,
    ComparisonDetailResponse,
    ProductPriceHistoryResponse,
)
from src.modules.products.schema.product import (
    PriceHistoryResponse,
    ProductListResponse,
    ProductResponse,
)
from src.modules.products.service.comparison_service import ComparisonService
from src.modules.products.service.product_service import ProductService
from src.modules.search.service.search_history_service import SearchHistoryService
from src.modules.shared import get_current_user
from src.modules.stores.service.store_service import StoreService

router = APIRouter(
    prefix="/api/products",
    tags=["products"],
    dependencies=[Depends(require_active_subscription)],
)


def _offer_to_response(offer, store_ref, is_cheapest: bool) -> ProductResponse:
    return ProductResponse(
        id=offer.id,
        store_id=offer.store_id,
        category_id=offer.category_id,
        product_id=offer.product_id,
        source_sku=offer.source_sku,
        title=offer.title,
        description=offer.description,
        image_url=offer.image_url,
        price_retail=offer.price_retail,
        price_opt=offer.price_opt,
        price_old=offer.price_old,
        currency=offer.currency,
        stock_status=offer.stock_status,
        stock_qty=offer.stock_qty,
        url=offer.url,
        last_seen_at=offer.last_seen_at,
        is_cheapest=is_cheapest,
        store=store_ref,
    )


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
    user=Depends(get_current_user),
):
    fuzzy = await is_fuzzy_enabled(db, user.id)
    offers, total = await ProductService.search(
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
        fuzzy=fuzzy,
    )

    if q.strip() and page == 1:
        await SearchHistoryService.record(
            db=db,
            user_id=user.id,
            query=q.strip(),
            filters={
                "store": store,
                "category": category,
                "min_price": min_price,
                "max_price": max_price,
                "in_stock": in_stock,
                "fuzzy": fuzzy,
            },
            results_count=total,
        )

    cheapest_price = None
    if offers:
        cheapest_price = min(o.price_retail for o in offers)

    results = []
    for offer in offers:
        store_obj = await StoreService.get_by_id(db, offer.store_id)
        store_ref = None
        if store_obj:
            store_ref = {"id": store_obj.id, "name": store_obj.name, "slug": store_obj.slug}
        results.append(
            _offer_to_response(
                offer,
                store_ref,
                cheapest_price is not None and offer.price_retail == cheapest_price,
            )
        )

    return ProductListResponse(results=results, total=total, page=page, per_page=per_page)


@router.get("/catalog", response_model=CatalogListResponse)
async def search_catalog(
    q: str = Query(default="", max_length=500),
    device_id: int | None = Query(default=None, ge=1),
    part_type_id: int | None = Query(default=None, ge=1),
    quality_tier_id: int | None = Query(default=None, ge=1),
    sort_by: str = Query(default="min_price_asc"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    results, total = await ComparisonService.search_catalog(
        db=db,
        query=q,
        device_id=device_id,
        part_type_id=part_type_id,
        quality_tier_id=quality_tier_id,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
    )
    return CatalogListResponse(results=results, total=total, page=page, per_page=per_page)


@router.get("/catalog/{product_id}", response_model=ComparisonDetailResponse)
async def get_catalog_product(
    product_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    comparison = await ComparisonService.get_comparison(db, product_id)
    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Canonical product not found"
        )
    return ComparisonDetailResponse(**comparison)


@router.get("/catalog/{product_id}/price-history", response_model=ProductPriceHistoryResponse)
async def get_catalog_price_history(
    product_id: int,
    days: int = Query(default=90, ge=1, le=730),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    points = await ComparisonService.get_price_history(db, product_id, days=days)
    if points is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Canonical product not found"
        )
    return ProductPriceHistoryResponse(product_id=product_id, days=days, points=points)


@router.get("/{offer_id}", response_model=ProductResponse)
async def get_product(
    offer_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    offer = await ProductService.get_by_id(db, offer_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    store_obj = await StoreService.get_by_id(db, offer.store_id)
    store_ref = None
    if store_obj:
        store_ref = {"id": store_obj.id, "name": store_obj.name, "slug": store_obj.slug}

    return _offer_to_response(offer, store_ref, False)


@router.get("/{offer_id}/price-history", response_model=list[PriceHistoryResponse])
async def get_price_history(
    offer_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    offer = await ProductService.get_by_id(db, offer_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return await ProductService.get_price_history(db, offer_id)
