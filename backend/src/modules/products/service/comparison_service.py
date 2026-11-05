import re
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.model.catalog import Brand, Device, DeviceAlias, PartType, QualityTier
from src.modules.products.model.product import (
    Cluster,
    OfferPriceHistory,
    Product,
    StoreOffer,
)
from src.modules.products.service.search_predicate import search_predicate
from src.modules.stores.model.store import Store

CATALOG_SORT_OPTIONS = ("min_price_asc", "min_price_desc")
CENTS = Decimal("0.01")


def _suggestion_display_name(
    canonical_name: str, device_name: str | None, brand_name: str | None
) -> str:
    if not device_name:
        return canonical_name
    label = device_name
    if brand_name and not label.casefold().startswith(brand_name.casefold()):
        label = f"{brand_name} {label}"
    for candidate in dict.fromkeys((label, device_name)):
        match = re.search(rf"(?<!\w){re.escape(candidate)}(?!\w)", canonical_name, re.IGNORECASE)
        if match is not None:
            start, end = match.span()
            remainder = " ".join(
                part.strip()
                for part in (canonical_name[:start], canonical_name[end:])
                if part.strip()
            )
            remainder = re.sub(r"\(\s*\)", "", remainder)
            remainder = re.sub(r"\s+([,;:])", r"\1", remainder)
            remainder = " ".join(remainder.split())
            return " ".join(part for part in (canonical_name[start:end], remainder) if part)
    return f"{label} {canonical_name}"


def _money(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def _offer_conditions(
    store_slug: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock: bool | None = None,
):
    filters = [
        StoreOffer.is_active.is_(True),
        Store.is_active.is_(True),
        StoreOffer.product_id.is_not(None),
    ]
    if store_slug is not None:
        filters.append(Store.slug == store_slug)
    if min_price is not None:
        filters.append(StoreOffer.price_retail >= min_price)
    if max_price is not None:
        filters.append(StoreOffer.price_retail <= max_price)
    if in_stock is not None:
        filters.append(
            StoreOffer.stock_status.in_(("in_stock", "low"))
            if in_stock
            else StoreOffer.stock_status == "out"
        )
    return filters


def _offer_source_subquery(
    store_slug: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock: bool | None = None,
):
    return (
        select(
            StoreOffer.product_id.label("product_id"),
            StoreOffer.id.label("source_offer_id"),
            StoreOffer.store_id.label("source_store_id"),
            Store.name.label("source_store_name"),
            Store.slug.label("source_store_slug"),
            StoreOffer.url.label("source_url"),
            func.row_number()
            .over(
                partition_by=StoreOffer.product_id,
                order_by=(StoreOffer.price_retail.asc(), StoreOffer.id.asc()),
            )
            .label("source_rank"),
        )
        .join(Store, Store.id == StoreOffer.store_id)
        .where(*_offer_conditions(store_slug, min_price, max_price, in_stock))
        .subquery()
    )


def _offer_aggregate_subquery(
    store_slug: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock: bool | None = None,
):
    filters = _offer_conditions(store_slug, min_price, max_price, in_stock)
    return (
        select(
            StoreOffer.product_id.label("product_id"),
            func.min(StoreOffer.price_retail).label("min_price_retail"),
            func.min(StoreOffer.price_opt).label("min_price_opt"),
            func.count(StoreOffer.id).label("offers_count"),
            func.count(func.distinct(StoreOffer.store_id)).label("stores_count"),
            func.array_agg(func.distinct(Store.slug)).label("store_slugs"),
            func.min(
                case(
                    (
                        func.trim(StoreOffer.image_url).op("~*")(r"^https?://[^[:space:]]+$"),
                        func.trim(StoreOffer.image_url),
                    ),
                    else_=None,
                )
            ).label("image_url"),
            case(
                (func.bool_or(StoreOffer.stock_status.in_(("in_stock", "low"))), "in_stock"),
                (func.bool_and(StoreOffer.stock_status == "out"), "out"),
                (func.bool_and(StoreOffer.stock_status == "preorder"), "preorder"),
                else_="unknown",
            ).label("stock_status"),
        )
        .join(Store, Store.id == StoreOffer.store_id)
        .where(*filters)
        .group_by(StoreOffer.product_id)
        .subquery()
    )


def _ref(entity, fields: tuple[str, ...]) -> dict | None:
    if entity is None:
        return None
    return {name: getattr(entity, name) for name in fields}


def _brand_ref(brand) -> dict | None:
    return _ref(brand, ("id", "name", "slug"))


def _device_ref(device) -> dict | None:
    return _ref(device, ("id", "name", "model_key", "brand_id"))


def _part_type_ref(part_type) -> dict | None:
    return _ref(part_type, ("id", "code", "name_ru"))


def _quality_ref(quality) -> dict | None:
    return _ref(quality, ("id", "code", "name_ru", "rank"))


def _cluster_ref(cluster) -> dict | None:
    if cluster is None:
        return None
    return {
        "id": cluster.id,
        "device_id": cluster.device_id,
        "part_type_id": cluster.part_type_id,
        "offers_count": cluster.offers_count,
        "min_price_retail": _money(cluster.min_price_retail),
        "min_price_opt": _money(cluster.min_price_opt),
    }


def _catalog_item(row) -> dict:
    product = row.Product
    return {
        "id": product.id,
        "canonical_key": product.canonical_key,
        "canonical_name": product.canonical_name,
        "image_url": row.image_url,
        "cluster_id": product.cluster_id,
        "key_attrs": product.key_attrs,
        "brand": _brand_ref(row.Brand),
        "device": _device_ref(row.Device),
        "part_type": _part_type_ref(row.PartType),
        "quality_tier": _quality_ref(row.QualityTier),
        "min_price_retail": _money(row.min_price_retail),
        "min_price_opt": _money(row.min_price_opt),
        "offers_count": row.offers_count or 0,
        "stores_count": row.stores_count or 0,
        "store_slugs": sorted(row.store_slugs or []),
        "stock_status": row.stock_status or "unknown",
        "source": (
            {
                "offer_id": row.source_offer_id,
                "store_id": row.source_store_id,
                "store_name": row.source_store_name,
                "store_slug": row.source_store_slug,
                "url": row.source_url,
            }
            if row.source_offer_id is not None
            else None
        ),
    }


class ComparisonService:
    @staticmethod
    async def device_suggestions(db: AsyncSession, query: str, limit: int = 6) -> list[dict]:
        query = query.strip()
        if len(query) < 2:
            return []
        alias_match = (
            select(DeviceAlias.id)
            .where(
                DeviceAlias.device_id == Device.id,
                search_predicate(func.concat(Brand.name, " ", DeviceAlias.alias), query),
            )
            .exists()
        )
        exact_alias = (
            select(DeviceAlias.id)
            .where(
                DeviceAlias.device_id == Device.id, func.lower(DeviceAlias.alias) == query.lower()
            )
            .exists()
        )
        rows = await db.execute(
            select(Device.id, Device.name, Device.model_key, func.count(Product.id).label("count"))
            .join(Brand, Brand.id == Device.brand_id)
            .join(Cluster, Cluster.device_id == Device.id)
            .join(Product, Product.cluster_id == Cluster.id)
            .where(
                or_(
                    search_predicate(func.concat(Brand.name, " ", Device.name), query),
                    alias_match,
                )
            )
            .group_by(Device.id)
            .order_by(
                case((or_(func.lower(Device.name) == query.lower(), exact_alias), 0), else_=1),
                func.length(Device.name),
                Device.name,
                Device.id,
            )
            .limit(limit)
        )
        return [
            {"id": row.id, "label": row.name, "model_key": row.model_key, "count": row.count}
            for row in rows
        ]

    @staticmethod
    async def catalog_facets(
        db: AsyncSession,
        query: str = "",
        fuzzy: bool = False,
        device_id: int | None = None,
        part_type_id: int | None = None,
        quality_tier_id: int | None = None,
        store_slug: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
    ) -> dict:
        agg = _offer_aggregate_subquery(store_slug, min_price, max_price, in_stock)
        filtered_offers = any(
            value is not None for value in (store_slug, min_price, max_price, in_stock)
        )

        def matching_products(dimension: str):
            stmt = (
                select(Product.id, Product.quality_tier_id, Cluster.device_id, Cluster.part_type_id)
                .select_from(Product)
                .outerjoin(Cluster, Cluster.id == Product.cluster_id)
            )
            if filtered_offers:
                stmt = stmt.join(agg, agg.c.product_id == Product.id)
            return ComparisonService._apply_filters(
                stmt,
                query,
                None if dimension == "device" else device_id,
                None if dimension == "part_type" else part_type_id,
                None if dimension == "quality" else quality_tier_id,
                fuzzy,
            ).subquery()

        products = matching_products("device")
        device_rows = await db.execute(
            select(Device.id, Device.name, func.count(products.c.id).label("count"))
            .outerjoin(products, products.c.device_id == Device.id)
            .group_by(Device.id)
            .having(or_(func.count(products.c.id) > 0, Device.id == device_id))
            .order_by(Device.name, Device.id)
        )
        products = matching_products("part_type")
        total = await db.scalar(select(func.count()).select_from(products))
        part_rows = await db.execute(
            select(PartType.id, PartType.name_ru, func.count(products.c.id).label("count"))
            .outerjoin(products, products.c.part_type_id == PartType.id)
            .group_by(PartType.id)
            .having(or_(func.count(products.c.id) > 0, PartType.id == part_type_id))
            .order_by(PartType.name_ru, PartType.id)
        )
        products = matching_products("quality")
        quality_rows = await db.execute(
            select(
                QualityTier.id,
                QualityTier.name_ru,
                QualityTier.rank,
                func.count(products.c.id).label("count"),
            )
            .outerjoin(products, products.c.quality_tier_id == QualityTier.id)
            .group_by(QualityTier.id)
            .having(or_(func.count(products.c.id) > 0, QualityTier.id == quality_tier_id))
            .order_by(QualityTier.rank, QualityTier.id)
        )
        return {
            "total": total or 0,
            "devices": [
                {"id": row.id, "label": row.name, "count": row.count} for row in device_rows
            ],
            "part_types": [
                {"id": row.id, "label": row.name_ru, "count": row.count} for row in part_rows
            ],
            "quality_tiers": [
                {"id": row.id, "label": row.name_ru, "count": row.count} for row in quality_rows
            ],
        }

    @staticmethod
    def _apply_filters(
        stmt,
        query: str,
        device_id: int | None,
        part_type_id: int | None,
        quality_tier_id: int | None,
        fuzzy: bool = False,
    ):
        stmt = stmt.where(search_predicate(Product.canonical_name, query, fuzzy))
        if device_id is not None:
            stmt = stmt.where(Cluster.device_id == device_id)
        if part_type_id is not None:
            stmt = stmt.where(Cluster.part_type_id == part_type_id)
        if quality_tier_id is not None:
            stmt = stmt.where(Product.quality_tier_id == quality_tier_id)
        return stmt

    @staticmethod
    async def search_catalog(
        db: AsyncSession,
        query: str = "",
        device_id: int | None = None,
        part_type_id: int | None = None,
        quality_tier_id: int | None = None,
        sort_by: str = "min_price_asc",
        page: int = 1,
        per_page: int = 20,
        store_slug: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
        fuzzy: bool = False,
    ) -> tuple[list[dict], int]:
        agg = _offer_aggregate_subquery(store_slug, min_price, max_price, in_stock)
        source = _offer_source_subquery(store_slug, min_price, max_price, in_stock)
        filtered_offers = any(
            value is not None for value in (store_slug, min_price, max_price, in_stock)
        )

        count_stmt = (
            select(func.count(Product.id))
            .select_from(Product)
            .outerjoin(Cluster, Cluster.id == Product.cluster_id)
        )
        if filtered_offers:
            count_stmt = count_stmt.join(agg, agg.c.product_id == Product.id)
        count_stmt = ComparisonService._apply_filters(
            count_stmt, query, device_id, part_type_id, quality_tier_id, fuzzy
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(
                Product,
                Cluster,
                QualityTier,
                Brand,
                Device,
                PartType,
                agg.c.min_price_retail,
                agg.c.min_price_opt,
                agg.c.offers_count,
                agg.c.stores_count,
                agg.c.store_slugs,
                agg.c.stock_status,
                agg.c.image_url,
                source.c.source_offer_id,
                source.c.source_store_id,
                source.c.source_store_name,
                source.c.source_store_slug,
                source.c.source_url,
            )
            .select_from(Product)
            .outerjoin(Cluster, Cluster.id == Product.cluster_id)
            .outerjoin(QualityTier, QualityTier.id == Product.quality_tier_id)
            .outerjoin(Brand, Brand.id == Product.brand_id)
            .outerjoin(Device, Device.id == Cluster.device_id)
            .outerjoin(PartType, PartType.id == Cluster.part_type_id)
            .outerjoin(agg, agg.c.product_id == Product.id)
            .outerjoin(
                source,
                (source.c.product_id == Product.id) & (source.c.source_rank == 1),
            )
        )
        if filtered_offers:
            stmt = stmt.where(agg.c.product_id.is_not(None))
        stmt = ComparisonService._apply_filters(
            stmt, query, device_id, part_type_id, quality_tier_id, fuzzy
        )

        if sort_by == "min_price_desc":
            order = agg.c.min_price_retail.desc().nullslast()
        else:
            order = agg.c.min_price_retail.asc().nullslast()

        offset = (page - 1) * per_page
        stmt = stmt.order_by(order, Product.id.asc()).offset(offset).limit(per_page)

        rows = (await db.execute(stmt)).all()
        return [_catalog_item(row) for row in rows], total

    @staticmethod
    async def suggestions(
        db: AsyncSession,
        query: str,
        limit: int = 6,
        fuzzy: bool = False,
        device_id: int | None = None,
        part_type_id: int | None = None,
        quality_tier_id: int | None = None,
        store_slug: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
    ) -> list[dict]:
        offers = (
            select(StoreOffer.id)
            .join(Store, Store.id == StoreOffer.store_id)
            .where(StoreOffer.product_id == Product.id)
            .where(*_offer_conditions(store_slug, min_price, max_price, in_stock))
            .exists()
        )
        stmt = (
            select(
                Product.id,
                Product.canonical_name,
                Device.name.label("device_name"),
                Brand.name.label("brand_name"),
            )
            .outerjoin(Cluster, Cluster.id == Product.cluster_id)
            .outerjoin(Device, Device.id == Cluster.device_id)
            .outerjoin(Brand, Brand.id == Device.brand_id)
            .where(offers)
        )
        stmt = ComparisonService._apply_filters(
            stmt, query, device_id, part_type_id, quality_tier_id, fuzzy
        )
        priority = case(
            (Product.canonical_name.ilike(f"{query.strip()}%"), 0),
            (search_predicate(Product.canonical_name, query, False), 1),
            else_=2,
        )
        rows = (
            await db.execute(
                stmt.order_by(priority, Product.canonical_name, Product.id).limit(limit)
            )
        ).all()
        return [
            {
                "id": row.id,
                "canonical_name": row.canonical_name,
                "display_name": _suggestion_display_name(
                    row.canonical_name, row.device_name, row.brand_name
                ),
            }
            for row in rows
        ]

    @staticmethod
    async def _load_product_row(db: AsyncSession, product_id: int):
        agg = _offer_aggregate_subquery()
        source = _offer_source_subquery()
        stmt = (
            select(
                Product,
                Cluster,
                QualityTier,
                Brand,
                Device,
                PartType,
                agg.c.min_price_retail,
                agg.c.min_price_opt,
                agg.c.offers_count,
                agg.c.stores_count,
                agg.c.store_slugs,
                agg.c.stock_status,
                agg.c.image_url,
                source.c.source_offer_id,
                source.c.source_store_id,
                source.c.source_store_name,
                source.c.source_store_slug,
                source.c.source_url,
            )
            .select_from(Product)
            .outerjoin(Cluster, Cluster.id == Product.cluster_id)
            .outerjoin(QualityTier, QualityTier.id == Product.quality_tier_id)
            .outerjoin(Brand, Brand.id == Product.brand_id)
            .outerjoin(Device, Device.id == Cluster.device_id)
            .outerjoin(PartType, PartType.id == Cluster.part_type_id)
            .outerjoin(agg, agg.c.product_id == Product.id)
            .outerjoin(
                source,
                (source.c.product_id == Product.id) & (source.c.source_rank == 1),
            )
            .where(Product.id == product_id)
        )
        return (await db.execute(stmt)).first()

    @staticmethod
    async def _load_offers(db: AsyncSession, product_id: int) -> list[dict]:
        stmt = (
            select(StoreOffer, Store)
            .join(Store, Store.id == StoreOffer.store_id)
            .where(StoreOffer.product_id == product_id)
            .where(StoreOffer.is_active.is_(True))
            .where(Store.is_active.is_(True))
            .order_by(StoreOffer.price_retail.asc(), StoreOffer.id.asc())
        )
        rows = (await db.execute(stmt)).all()

        offers = []
        for offer, store in rows:
            offers.append(
                {
                    "id": offer.id,
                    "store_id": offer.store_id,
                    "source_sku": offer.source_sku,
                    "title": offer.title,
                    "price_retail": _money(offer.price_retail),
                    "price_opt": _money(offer.price_opt),
                    "price_old": _money(offer.price_old),
                    "currency": offer.currency,
                    "stock_status": offer.stock_status,
                    "stock_qty": offer.stock_qty,
                    "url": offer.url,
                    "match_status": offer.match_status,
                    "match_confidence": offer.match_confidence,
                    "last_seen_at": offer.last_seen_at,
                    "price_changed_at": offer.price_changed_at,
                    "is_cheapest": False,
                    "store": {"id": store.id, "name": store.name, "slug": store.slug},
                }
            )

        if offers:
            cheapest = offers[0]["price_retail"]
            for item in offers:
                item["is_cheapest"] = item["price_retail"] == cheapest

        return offers

    @staticmethod
    def _build_stats(offers: list[dict]) -> dict:
        if not offers:
            return {
                "offers_count": 0,
                "stores_count": 0,
                "min_price_retail": None,
                "max_price_retail": None,
                "avg_price_retail": None,
                "min_price_opt": None,
                "spread_abs": None,
                "spread_pct": None,
            }

        retail = [item["price_retail"] for item in offers]
        opt = [item["price_opt"] for item in offers if item["price_opt"] is not None]
        minimum = min(retail)
        maximum = max(retail)
        average = _money(sum(retail) / Decimal(len(retail)))
        spread_abs = _money(maximum - minimum)
        spread_pct = None
        if minimum > 0:
            spread_pct = float(
                (spread_abs / minimum * Decimal(100)).quantize(CENTS, rounding=ROUND_HALF_UP)
            )

        return {
            "offers_count": len(offers),
            "stores_count": len({item["store_id"] for item in offers}),
            "min_price_retail": minimum,
            "max_price_retail": maximum,
            "avg_price_retail": average,
            "min_price_opt": min(opt) if opt else None,
            "spread_abs": spread_abs,
            "spread_pct": spread_pct,
        }

    @staticmethod
    async def _load_alternatives(
        db: AsyncSession, cluster_id: int | None, product_id: int
    ) -> list[dict]:
        if cluster_id is None:
            return []

        agg = _offer_aggregate_subquery()
        stmt = (
            select(
                Product,
                QualityTier,
                agg.c.min_price_retail,
                agg.c.min_price_opt,
                agg.c.offers_count,
                agg.c.stores_count,
            )
            .select_from(Product)
            .outerjoin(QualityTier, QualityTier.id == Product.quality_tier_id)
            .outerjoin(agg, agg.c.product_id == Product.id)
            .where(Product.cluster_id == cluster_id)
            .where(Product.id != product_id)
            .order_by(agg.c.min_price_retail.asc().nullslast(), Product.id.asc())
        )
        rows = (await db.execute(stmt)).all()

        return [
            {
                "product_id": row.Product.id,
                "canonical_key": row.Product.canonical_key,
                "canonical_name": row.Product.canonical_name,
                "quality_tier": _quality_ref(row.QualityTier),
                "min_price_retail": _money(row.min_price_retail),
                "min_price_opt": _money(row.min_price_opt),
                "offers_count": row.offers_count or 0,
                "stores_count": row.stores_count or 0,
            }
            for row in rows
        ]

    @staticmethod
    async def get_comparison(db: AsyncSession, product_id: int) -> dict | None:
        row = await ComparisonService._load_product_row(db, product_id)
        if row is None:
            return None

        offers = await ComparisonService._load_offers(db, product_id)
        alternatives = await ComparisonService._load_alternatives(
            db, row.Product.cluster_id, product_id
        )

        return {
            "product": _catalog_item(row),
            "cluster": _cluster_ref(row.Cluster),
            "offers": offers,
            "stats": ComparisonService._build_stats(offers),
            "alternatives": alternatives,
        }

    @staticmethod
    async def product_exists(db: AsyncSession, product_id: int) -> bool:
        result = await db.execute(select(Product.id).where(Product.id == product_id))
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_price_history(
        db: AsyncSession, product_id: int, days: int = 90
    ) -> list[dict] | None:
        if not await ComparisonService.product_exists(db, product_id):
            return None

        since = datetime.now(timezone.utc) - timedelta(days=days)
        day = func.date(func.timezone("UTC", OfferPriceHistory.recorded_at)).label("day")

        stmt = (
            select(
                day,
                func.min(OfferPriceHistory.price_retail).label("min_price_retail"),
                func.max(OfferPriceHistory.price_retail).label("max_price_retail"),
                func.avg(OfferPriceHistory.price_retail).label("avg_price_retail"),
                func.count(func.distinct(StoreOffer.store_id)).label("stores_count"),
            )
            .select_from(OfferPriceHistory)
            .join(StoreOffer, StoreOffer.id == OfferPriceHistory.offer_id)
            .join(Store, Store.id == StoreOffer.store_id)
            .where(StoreOffer.product_id == product_id)
            .where(Store.is_active.is_(True))
            .where(OfferPriceHistory.recorded_at >= since)
            .group_by(day)
            .order_by(day)
        )
        rows = (await db.execute(stmt)).all()

        return [
            {
                "day": row.day,
                "min_price_retail": _money(row.min_price_retail),
                "max_price_retail": _money(row.max_price_retail),
                "avg_price_retail": _money(row.avg_price_retail),
                "stores_count": row.stores_count or 0,
            }
            for row in rows
        ]
