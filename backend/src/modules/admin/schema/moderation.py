from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.modules.products.schema.product import StoreRef

CANDIDATE_STATUS_FILTERS = ("pending", "approved", "rejected", "all")


class ModerationOfferRef(BaseModel):
    id: int
    store_id: int
    source_sku: str
    title: str
    normalized_title: str
    price_retail: Decimal
    price_opt: Decimal | None = None
    price_old: Decimal | None = None
    currency: str
    stock_status: str
    url: str
    image_url: str | None = None
    is_active: bool
    product_id: int | None = None
    match_status: str
    match_confidence: Decimal | None = None
    last_seen_at: datetime
    store: StoreRef | None = None

    model_config = {"from_attributes": True}


class ModerationProductRef(BaseModel):
    id: int
    canonical_key: str
    canonical_name: str
    cluster_id: int | None = None
    brand_id: int | None = None
    quality_tier_id: int | None = None
    key_attrs: dict | None = None

    model_config = {"from_attributes": True}


class MatchCandidateResponse(BaseModel):
    id: int
    offer_id: int
    product_id: int
    score: Decimal
    features: dict | None = None
    status: str
    decided_by: int | None = None
    decided_at: datetime | None = None
    created_at: datetime
    offer: ModerationOfferRef | None = None
    product: ModerationProductRef | None = None

    model_config = {"from_attributes": True}


class MatchCandidateListResponse(BaseModel):
    results: list[MatchCandidateResponse]
    total: int
    page: int
    per_page: int


class ReviewOfferListResponse(BaseModel):
    results: list[ModerationOfferRef]
    total: int
    page: int
    per_page: int


class OfferStateResponse(BaseModel):
    id: int
    product_id: int | None = None
    match_status: str
    match_confidence: Decimal | None = None

    model_config = {"from_attributes": True}


class CandidateDecisionResponse(BaseModel):
    candidate: MatchCandidateResponse
    offer: OfferStateResponse
    rejected_candidate_ids: list[int] = []


class OfferLinkRequest(BaseModel):
    product_id: int = Field(..., ge=1)

    model_config = {"extra": "ignore"}


class OfferLinkResponse(BaseModel):
    offer: OfferStateResponse
    rejected_candidate_ids: list[int] = []
