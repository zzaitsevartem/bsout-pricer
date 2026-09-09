import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.parser.service.base import parser_manager
from src.modules.parser.service.exceptions import ParserParseError
from src.modules.parser.service.parser_service import parser_service
from src.modules.products.model.product import StoreOffer
from src.modules.stores.model.store import Store
from src.modules.tracking.model.tracking import TrackedProduct

logger = logging.getLogger(__name__)

MAX_OFFERS_PER_RUN = 500


async def tracked_offer_urls(db: AsyncSession, limit: int = MAX_OFFERS_PER_RUN) -> list[tuple]:
    stmt = (
        select(StoreOffer.id, StoreOffer.url, Store.slug, Store.id)
        .join(Store, Store.id == StoreOffer.store_id)
        .join(TrackedProduct, TrackedProduct.product_id == StoreOffer.product_id)
        .where(
            TrackedProduct.is_active.is_(True),
            StoreOffer.is_active.is_(True),
            StoreOffer.url.isnot(None),
            StoreOffer.url != "",
        )
        .distinct()
        .limit(limit)
    )
    return [tuple(row) for row in (await db.execute(stmt)).all()]


async def refresh_tracked_offers(db: AsyncSession, limit: int = MAX_OFFERS_PER_RUN) -> dict:
    rows = await tracked_offer_urls(db, limit=limit)
    refreshed = 0
    failed = 0
    skipped_no_parser = 0

    for _offer_id, url, store_slug, store_id in rows:
        parser = parser_manager.get(store_slug)
        if parser is None:
            skipped_no_parser += 1
            continue
        try:
            result = await parser.parse_product(url)
        except Exception as exc:
            failed += 1
            logger.warning("price refresh failed for %s: %s", url, exc)
            continue
        if result is None:
            failed += 1
            continue
        try:
            await parser_service.upsert_offer(db, store_id, result)
        except ParserParseError as exc:
            failed += 1
            logger.warning("price refresh rejected %s: %s", url, exc)
            continue
        refreshed += 1

    await db.commit()
    return {
        "candidates": len(rows),
        "refreshed": refreshed,
        "failed": failed,
        "skipped_no_parser": skipped_no_parser,
    }
