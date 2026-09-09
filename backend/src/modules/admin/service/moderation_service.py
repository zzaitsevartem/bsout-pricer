from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.admin.schema.moderation import (
    CandidateDecisionResponse,
    MatchCandidateResponse,
    ModerationOfferRef,
    ModerationProductRef,
    OfferLinkResponse,
    OfferStateResponse,
)
from src.modules.products.model.product import MatchCandidate, Product, StoreOffer
from src.modules.products.schema.product import StoreRef
from src.modules.stores.model.store import Store

CONFIDENCE_QUANT = Decimal("0.0001")
MANUAL_CONFIDENCE = Decimal("1.0000")


class ModerationError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _confidence(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value).quantize(CONFIDENCE_QUANT, rounding=ROUND_HALF_UP)


def _offer_ref(offer: StoreOffer, store: Store | None) -> ModerationOfferRef:
    ref = ModerationOfferRef.model_validate(offer)
    ref.store = StoreRef.model_validate(store) if store is not None else None
    return ref


def _candidate_response(
    candidate: MatchCandidate,
    offer: StoreOffer | None,
    store: Store | None,
    product: Product | None,
) -> MatchCandidateResponse:
    response = MatchCandidateResponse.model_validate(candidate)
    response.offer = _offer_ref(offer, store) if offer is not None else None
    response.product = ModerationProductRef.model_validate(product) if product is not None else None
    return response


class ModerationService:
    @staticmethod
    async def list_candidates(
        db: AsyncSession,
        *,
        status: str = "pending",
        offer_id: int | None = None,
        product_id: int | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[MatchCandidateResponse], int]:
        filters = []
        if status != "all":
            filters.append(MatchCandidate.status == status)
        if offer_id is not None:
            filters.append(MatchCandidate.offer_id == offer_id)
        if product_id is not None:
            filters.append(MatchCandidate.product_id == product_id)

        total_stmt = select(func.count()).select_from(MatchCandidate)
        for condition in filters:
            total_stmt = total_stmt.where(condition)
        total = (await db.execute(total_stmt)).scalar() or 0

        stmt = (
            select(MatchCandidate, StoreOffer, Store, Product)
            .join(StoreOffer, StoreOffer.id == MatchCandidate.offer_id)
            .join(Store, Store.id == StoreOffer.store_id)
            .join(Product, Product.id == MatchCandidate.product_id)
        )
        for condition in filters:
            stmt = stmt.where(condition)
        stmt = (
            stmt.order_by(MatchCandidate.score.desc(), MatchCandidate.id.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        rows = (await db.execute(stmt)).all()
        results = [
            _candidate_response(candidate, offer, store, product)
            for candidate, offer, store, product in rows
        ]
        return results, total

    @staticmethod
    async def list_review_offers(
        db: AsyncSession, *, page: int = 1, per_page: int = 20
    ) -> tuple[list[ModerationOfferRef], int]:
        total = (
            await db.execute(
                select(func.count())
                .select_from(StoreOffer)
                .where(StoreOffer.match_status == "review")
            )
        ).scalar() or 0

        stmt = (
            select(StoreOffer, Store)
            .join(Store, Store.id == StoreOffer.store_id)
            .where(StoreOffer.match_status == "review")
            .order_by(StoreOffer.last_seen_at.desc(), StoreOffer.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        rows = (await db.execute(stmt)).all()
        return [_offer_ref(offer, store) for offer, store in rows], total

    @staticmethod
    async def _get_store(db: AsyncSession, store_id: int) -> Store | None:
        return await db.get(Store, store_id)

    @staticmethod
    async def _pending_siblings(
        db: AsyncSession, offer_id: int, exclude_id: int | None = None
    ) -> list[MatchCandidate]:
        stmt = select(MatchCandidate).where(
            MatchCandidate.offer_id == offer_id,
            MatchCandidate.status == "pending",
        )
        if exclude_id is not None:
            stmt = stmt.where(MatchCandidate.id != exclude_id)
        return list((await db.execute(stmt.order_by(MatchCandidate.id))).scalars().all())

    @classmethod
    async def _close_pending_siblings(
        cls,
        db: AsyncSession,
        offer_id: int,
        admin_id: int,
        decided_at: datetime,
        exclude_id: int | None = None,
    ) -> list[int]:
        siblings = await cls._pending_siblings(db, offer_id, exclude_id)
        for sibling in siblings:
            sibling.status = "rejected"
            sibling.decided_by = admin_id
            sibling.decided_at = decided_at
        return [sibling.id for sibling in siblings]

    @staticmethod
    async def _load_candidate(db: AsyncSession, candidate_id: int) -> MatchCandidate:
        candidate = await db.get(MatchCandidate, candidate_id)
        if candidate is None:
            raise ModerationError(404, "Match candidate not found")
        return candidate

    @staticmethod
    def _ensure_pending(candidate: MatchCandidate) -> None:
        if candidate.status != "pending":
            raise ModerationError(409, f"Candidate already {candidate.status}")

    @staticmethod
    async def _load_offer(db: AsyncSession, offer_id: int) -> StoreOffer:
        offer = await db.get(StoreOffer, offer_id)
        if offer is None:
            raise ModerationError(404, "Offer not found")
        return offer

    @staticmethod
    async def _load_product(db: AsyncSession, product_id: int) -> Product:
        product = await db.get(Product, product_id)
        if product is None:
            raise ModerationError(404, "Product not found")
        return product

    @classmethod
    async def approve(
        cls, db: AsyncSession, candidate_id: int, admin_id: int
    ) -> CandidateDecisionResponse:
        candidate = await cls._load_candidate(db, candidate_id)
        cls._ensure_pending(candidate)

        offer = await cls._load_offer(db, candidate.offer_id)
        product = await cls._load_product(db, candidate.product_id)
        decided_at = _now()

        offer.product_id = product.id
        offer.match_status = "manual"
        offer.match_confidence = _confidence(candidate.score)

        candidate.status = "approved"
        candidate.decided_by = admin_id
        candidate.decided_at = decided_at

        rejected_ids = await cls._close_pending_siblings(
            db, offer.id, admin_id, decided_at, exclude_id=candidate.id
        )
        await db.flush()

        store = await cls._get_store(db, offer.store_id)
        return CandidateDecisionResponse(
            candidate=_candidate_response(candidate, offer, store, product),
            offer=OfferStateResponse.model_validate(offer),
            rejected_candidate_ids=rejected_ids,
        )

    @classmethod
    async def reject(
        cls, db: AsyncSession, candidate_id: int, admin_id: int
    ) -> CandidateDecisionResponse:
        candidate = await cls._load_candidate(db, candidate_id)
        cls._ensure_pending(candidate)

        offer = await cls._load_offer(db, candidate.offer_id)
        candidate.status = "rejected"
        candidate.decided_by = admin_id
        candidate.decided_at = _now()
        await db.flush()

        product = await db.get(Product, candidate.product_id)
        store = await cls._get_store(db, offer.store_id)
        return CandidateDecisionResponse(
            candidate=_candidate_response(candidate, offer, store, product),
            offer=OfferStateResponse.model_validate(offer),
            rejected_candidate_ids=[],
        )

    @classmethod
    async def link_offer(
        cls, db: AsyncSession, offer_id: int, product_id: int, admin_id: int
    ) -> OfferLinkResponse:
        offer = await cls._load_offer(db, offer_id)
        product = await cls._load_product(db, product_id)
        decided_at = _now()

        offer.product_id = product.id
        offer.match_status = "manual"
        offer.match_confidence = MANUAL_CONFIDENCE

        rejected_ids = await cls._close_pending_siblings(db, offer.id, admin_id, decided_at)
        await db.flush()

        return OfferLinkResponse(
            offer=OfferStateResponse.model_validate(offer),
            rejected_candidate_ids=rejected_ids,
        )

    @classmethod
    async def unlink_offer(
        cls, db: AsyncSession, offer_id: int, admin_id: int
    ) -> OfferLinkResponse:
        offer = await cls._load_offer(db, offer_id)
        decided_at = _now()

        offer.product_id = None
        offer.match_status = "rejected"
        offer.match_confidence = None

        rejected_ids = await cls._close_pending_siblings(db, offer.id, admin_id, decided_at)
        await db.flush()

        return OfferLinkResponse(
            offer=OfferStateResponse.model_validate(offer),
            rejected_candidate_ids=rejected_ids,
        )
