import re
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.model.catalog import Brand, Device, PartType, QualityTier
from src.modules.catalog.service.dictionaries import Dictionaries, load_dictionaries
from src.modules.catalog.service.extractor import UNKNOWN_QUALITY_CODE, ExtractedAttrs, extract
from src.modules.products.model.product import Cluster, MatchCandidate, Product, StoreOffer

AUTO_THRESHOLD = 0.8
CANDIDATE_THRESHOLD = 0.5
PROTECTED_STATUSES = ("manual", "rejected")

_DEVICE_PHRASE_RE = re.compile(r"(?:для|for)\s+(.+?)(?:\s*\(|\+|,|$)", re.IGNORECASE)

_MODEL_SUFFIXES = ("plus", "ultra", "pro", "max", "fe", "mini", "lite", "nfc")
_SUFFIX_RE = re.compile(r"\b(" + "|".join(_MODEL_SUFFIXES) + r")\b", re.IGNORECASE)


@dataclass(frozen=True)
class MatchOutcome:
    offer_id: int
    product_id: int | None
    status: str
    confidence: float


@dataclass
class MatchStats:
    processed: int = 0
    auto: int = 0
    candidates: int = 0
    review: int = 0
    unmatched: int = 0
    skipped: int = 0
    products_created: int = 0
    clusters_created: int = 0

    def as_dict(self) -> dict:
        return {
            "processed": self.processed,
            "auto": self.auto,
            "candidates": self.candidates,
            "review": self.review,
            "unmatched": self.unmatched,
            "skipped": self.skipped,
            "products_created": self.products_created,
            "clusters_created": self.clusters_created,
        }


class MatchingService:
    @staticmethod
    def build_canonical_key(
        model_key: str, part_type_code: str, quality_code: str, color_code: str | None
    ) -> str:
        return f"{model_key}|{part_type_code}|{quality_code}|{color_code or '-'}"

    @staticmethod
    async def _get_or_create_cluster(
        db: AsyncSession, device_id: int, part_type_id: int, stats: MatchStats | None
    ) -> Cluster:
        existing = (
            await db.execute(
                select(Cluster).where(
                    Cluster.device_id == device_id,
                    Cluster.part_type_id == part_type_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        cluster = Cluster(device_id=device_id, part_type_id=part_type_id)
        db.add(cluster)
        await db.flush()
        if stats is not None:
            stats.clusters_created += 1
        return cluster

    @staticmethod
    async def canonicalize(
        db: AsyncSession,
        attrs: ExtractedAttrs,
        dicts: Dictionaries,
        stats: MatchStats | None = None,
    ) -> Product | None:
        if attrs.device_id is None or attrs.part_type_id is None:
            return None

        model_key = dicts.device_model_key.get(attrs.device_id)
        part_type_code = dicts.part_type_code.get(attrs.part_type_id)
        if model_key is None or part_type_code is None:
            return None

        quality_code = (
            dicts.quality_code.get(attrs.quality_tier_id)
            if attrs.quality_tier_id is not None
            else None
        ) or UNKNOWN_QUALITY_CODE
        color_code = dicts.color_code.get(attrs.color_id) if attrs.color_id is not None else None

        canonical_key = MatchingService.build_canonical_key(
            model_key, part_type_code, quality_code, color_code
        )

        existing = (
            await db.execute(select(Product).where(Product.canonical_key == canonical_key))
        ).scalar_one_or_none()
        if existing is not None:
            refreshed_name = await MatchingService._build_canonical_name(db, attrs)
            if refreshed_name and existing.canonical_name != refreshed_name:
                existing.canonical_name = refreshed_name
                await db.flush()
            return existing

        cluster = await MatchingService._get_or_create_cluster(
            db, attrs.device_id, attrs.part_type_id, stats
        )
        canonical_name = await MatchingService._build_canonical_name(db, attrs)

        product = Product(
            cluster_id=cluster.id,
            quality_tier_id=attrs.quality_tier_id,
            brand_id=attrs.brand_id,
            key_attrs={
                "device_id": attrs.device_id,
                "part_type_id": attrs.part_type_id,
                "quality_tier_id": attrs.quality_tier_id,
                "color_id": attrs.color_id,
                "matched": attrs.matched,
            },
            canonical_key=canonical_key,
            canonical_name=canonical_name,
        )
        db.add(product)
        await db.flush()
        if stats is not None:
            stats.products_created += 1
        return product

    @staticmethod
    def _short_quality(name_ru: str) -> str:
        for separator in (" (", " / "):
            if separator in name_ru:
                return name_ru.split(separator)[0].strip()
        return name_ru.strip()

    @staticmethod
    async def _build_canonical_name(db: AsyncSession, attrs: ExtractedAttrs) -> str:
        device_row = (
            await db.execute(
                select(Device.name, Brand.name)
                .join(Brand, Brand.id == Device.brand_id)
                .where(Device.id == attrs.device_id)
            )
        ).first()
        part_type_name = (
            await db.execute(select(PartType.name_ru).where(PartType.id == attrs.part_type_id))
        ).scalar_one_or_none()

        quality_name = None
        if attrs.quality_tier_id is not None:
            raw_quality = (
                await db.execute(
                    select(QualityTier.name_ru, QualityTier.code).where(
                        QualityTier.id == attrs.quality_tier_id
                    )
                )
            ).first()
            if raw_quality is not None and raw_quality[1] != UNKNOWN_QUALITY_CODE:
                quality_name = MatchingService._short_quality(raw_quality[0])

        device_name, brand_name = device_row if device_row is not None else (None, None)
        device_label = device_name or ""
        if brand_name and device_label and not device_label.lower().startswith(brand_name.lower()):
            device_label = f"{brand_name} {device_label}"

        parts = [part_type_name or "Деталь", device_label]
        name = " ".join(part for part in parts if part).strip()
        if quality_name:
            name = f"{name} ({quality_name})"
        return name[:500]

    @staticmethod
    async def match_offer(
        db: AsyncSession,
        offer: StoreOffer,
        dicts: Dictionaries,
        stats: MatchStats | None = None,
    ) -> MatchOutcome:
        if offer.match_status in PROTECTED_STATUSES:
            if stats is not None:
                stats.skipped += 1
            return MatchOutcome(offer.id, offer.product_id, offer.match_status, 0.0)

        attrs = extract(offer.title, dicts)
        confidence = round(float(attrs.confidence), 4)

        if stats is not None:
            stats.processed += 1

        product = None
        if confidence >= CANDIDATE_THRESHOLD:
            product = await MatchingService.canonicalize(db, attrs, dicts, stats)

        if product is None:
            if attrs.part_type_id is not None or attrs.device_id is not None:
                offer.match_status = "review"
                offer.match_confidence = confidence
                await db.flush()
                if stats is not None:
                    stats.review += 1
                return MatchOutcome(offer.id, None, "review", confidence)
            if stats is not None:
                stats.unmatched += 1
            return MatchOutcome(offer.id, None, "unmatched", confidence)

        if confidence >= AUTO_THRESHOLD:
            offer.product_id = product.id
            offer.match_status = "auto"
            offer.match_confidence = confidence
            await db.flush()
            if stats is not None:
                stats.auto += 1
            return MatchOutcome(offer.id, product.id, "auto", confidence)

        await MatchingService._ensure_candidate(db, offer, product, confidence, attrs)
        if stats is not None:
            stats.candidates += 1
        return MatchOutcome(offer.id, None, "candidate", confidence)

    @staticmethod
    async def _ensure_candidate(
        db: AsyncSession,
        offer: StoreOffer,
        product: Product,
        confidence: float,
        attrs: ExtractedAttrs,
    ) -> None:
        existing = (
            await db.execute(
                select(MatchCandidate).where(
                    MatchCandidate.offer_id == offer.id,
                    MatchCandidate.product_id == product.id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            if existing.status == "pending":
                existing.score = confidence
                existing.features = dict(attrs.matched)
                await db.flush()
            return

        db.add(
            MatchCandidate(
                offer_id=offer.id,
                product_id=product.id,
                score=confidence,
                features=dict(attrs.matched),
                status="pending",
            )
        )
        await db.flush()

    @staticmethod
    def _offers_query(only_unmatched: bool, limit: int | None) -> Select:
        query = select(StoreOffer).where(StoreOffer.match_status.notin_(PROTECTED_STATUSES))
        if only_unmatched:
            query = query.where(StoreOffer.product_id.is_(None))
        query = query.order_by(StoreOffer.id)
        if limit is not None:
            query = query.limit(limit)
        return query

    @staticmethod
    async def match_all(
        db: AsyncSession, only_unmatched: bool = True, limit: int | None = None
    ) -> dict:
        dicts = await load_dictionaries(db)
        stats = MatchStats()

        offers = (
            (await db.execute(MatchingService._offers_query(only_unmatched, limit))).scalars().all()
        )
        for offer in offers:
            await MatchingService.match_offer(db, offer, dicts, stats)

        await MatchingService.recalc_cluster_aggregates(db)
        return stats.as_dict()

    @staticmethod
    async def device_gap_report(db: AsyncSession, limit: int = 30) -> list[tuple[str, int]]:
        titles = (
            (await db.execute(select(StoreOffer.title).where(StoreOffer.match_status == "review")))
            .scalars()
            .all()
        )
        counter: Counter[str] = Counter()
        for title in titles:
            match = _DEVICE_PHRASE_RE.search(title)
            phrase = (match.group(1).strip() if match else title).strip()[:60]
            if phrase:
                counter[phrase] += 1
        return counter.most_common(limit)

    @staticmethod
    async def precision_report(db: AsyncSession, limit: int = 30) -> list[dict]:
        rows = (
            await db.execute(
                select(StoreOffer.id, StoreOffer.title, Device.name, Device.id)
                .join(Product, Product.id == StoreOffer.product_id)
                .join(Cluster, Cluster.id == Product.cluster_id)
                .join(Device, Device.id == Cluster.device_id)
                .where(StoreOffer.match_status == "auto", StoreOffer.is_active.is_(True))
            )
        ).all()

        suspicious: list[dict] = []
        for offer_id, title, device_name, device_id in rows:
            in_title = {m.lower() for m in _SUFFIX_RE.findall(title or "")}
            in_device = {m.lower() for m in _SUFFIX_RE.findall(device_name or "")}
            missing = sorted(in_title - in_device)
            if missing:
                suspicious.append(
                    {
                        "offer_id": offer_id,
                        "title": (title or "")[:90],
                        "device": device_name,
                        "device_id": device_id,
                        "missing": missing,
                    }
                )
        suspicious.sort(key=lambda row: (len(row["missing"]), row["device"]), reverse=True)
        return suspicious[:limit]

    @staticmethod
    async def precision_stats(db: AsyncSession) -> dict:
        total = (
            await db.execute(
                select(func.count())
                .select_from(StoreOffer)
                .where(StoreOffer.match_status == "auto", StoreOffer.is_active.is_(True))
            )
        ).scalar() or 0
        suspicious = await MatchingService.precision_report(db, limit=10**6)
        share = round(100.0 * len(suspicious) / total, 2) if total else 0.0
        return {"auto": total, "suspicious": len(suspicious), "share_pct": share}

    @staticmethod
    async def recalc_cluster_aggregates(
        db: AsyncSession, cluster_ids: list[int] | None = None
    ) -> int:
        aggregates = (
            select(
                Product.cluster_id.label("cluster_id"),
                func.count(StoreOffer.id).label("offers_count"),
                func.min(StoreOffer.price_retail).label("min_price_retail"),
                func.min(StoreOffer.price_opt).label("min_price_opt"),
            )
            .select_from(StoreOffer)
            .join(Product, Product.id == StoreOffer.product_id)
            .where(StoreOffer.is_active.is_(True), Product.cluster_id.is_not(None))
            .group_by(Product.cluster_id)
        )
        if cluster_ids:
            aggregates = aggregates.where(Product.cluster_id.in_(cluster_ids))
        subquery = aggregates.subquery()

        reset = update(Cluster).values(offers_count=0, min_price_retail=None, min_price_opt=None)
        if cluster_ids:
            reset = reset.where(Cluster.id.in_(cluster_ids))
        await db.execute(reset)

        result = await db.execute(
            update(Cluster)
            .where(Cluster.id == subquery.c.cluster_id)
            .values(
                offers_count=subquery.c.offers_count,
                min_price_retail=subquery.c.min_price_retail,
                min_price_opt=subquery.c.min_price_opt,
            )
        )
        await db.flush()
        return result.rowcount or 0
