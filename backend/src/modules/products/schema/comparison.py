from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from src.modules.products.schema.product import StoreRef


class BrandRef(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class DeviceRef(BaseModel):
    id: int
    name: str
    model_key: str
    brand_id: int

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class PartTypeRef(BaseModel):
    id: int
    code: str
    name_ru: str

    model_config = {"from_attributes": True}


class QualityTierRef(BaseModel):
    id: int
    code: str
    name_ru: str
    rank: int

    model_config = {"from_attributes": True}


class ClusterRef(BaseModel):
    id: int
    device_id: int
    part_type_id: int
    offers_count: int
    min_price_retail: Decimal | None = None
    min_price_opt: Decimal | None = None

    model_config = {"from_attributes": True}


class CatalogItemResponse(BaseModel):
    id: int
    canonical_key: str
    canonical_name: str
    cluster_id: int | None = None
    key_attrs: dict | None = None
    brand: BrandRef | None = None
    device: DeviceRef | None = None
    part_type: PartTypeRef | None = None
    quality_tier: QualityTierRef | None = None
    min_price_retail: Decimal | None = None
    min_price_opt: Decimal | None = None
    offers_count: int = 0
    stores_count: int = 0
    store_slugs: list[str] = []


class CatalogListResponse(BaseModel):
    results: list[CatalogItemResponse]
    total: int
    page: int
    per_page: int


class ComparisonOfferResponse(BaseModel):
    id: int
    store_id: int
    source_sku: str
    title: str
    price_retail: Decimal
    price_opt: Decimal | None = None
    price_old: Decimal | None = None
    currency: str
    stock_status: str
    stock_qty: int | None = None
    url: str
    match_status: str
    match_confidence: Decimal | None = None
    last_seen_at: datetime
    price_changed_at: datetime | None = None
    is_cheapest: bool = False
    store: StoreRef | None = None


class ComparisonStatsResponse(BaseModel):
    offers_count: int
    stores_count: int
    min_price_retail: Decimal | None = None
    max_price_retail: Decimal | None = None
    avg_price_retail: Decimal | None = None
    min_price_opt: Decimal | None = None
    spread_abs: Decimal | None = None
    spread_pct: float | None = None


class AlternativeTierResponse(BaseModel):
    product_id: int
    canonical_key: str
    canonical_name: str
    quality_tier: QualityTierRef | None = None
    min_price_retail: Decimal | None = None
    min_price_opt: Decimal | None = None
    offers_count: int = 0
    stores_count: int = 0


class ComparisonDetailResponse(BaseModel):
    product: CatalogItemResponse
    cluster: ClusterRef | None = None
    offers: list[ComparisonOfferResponse]
    stats: ComparisonStatsResponse
    alternatives: list[AlternativeTierResponse]


class PricePointResponse(BaseModel):
    day: date
    min_price_retail: Decimal
    max_price_retail: Decimal | None = None
    avg_price_retail: Decimal | None = None
    stores_count: int


class ProductPriceHistoryResponse(BaseModel):
    product_id: int
    days: int
    points: list[PricePointResponse]
