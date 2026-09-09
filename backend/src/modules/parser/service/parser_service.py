import asyncio
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory
from src.modules.cache import RedisCache
from src.modules.parser.service.base import BaseParser, ParseResult, ParserManager, parser_manager
from src.modules.parser.service.exceptions import ParserError, ParserParseError
from src.modules.parser.service.queue import enqueue_parser_run
from src.modules.parser.service.utils import normalize_name
from src.modules.products.model.product import OfferPriceHistory, StoreOffer
from src.modules.stores.model.store import Store

STATUS_TTL = 86400
QUEUED_STATUS_TTL = 900
LOCK_TTL = 3600
FULL_SYNC_LOCK_TTL = 6 * 3600
DEFAULT_RUN_LIMIT = 500
MIN_DEACTIVATION_COVERAGE = 0.8


def _status_key(slug: str) -> str:
    return f"parser:status:{slug}"


def _lock_key(slug: str) -> str:
    return f"parser:lock:{slug}"


def resolve_catalog_limit(full_sync: bool, limit: int | None) -> int | None:
    if limit is not None:
        return limit
    return None if full_sync else DEFAULT_RUN_LIMIT


def resolve_lock_ttl(catalog_limit: int | None) -> int:
    return LOCK_TTL if catalog_limit is not None else FULL_SYNC_LOCK_TTL


def _running_status(slug: str, parser: BaseParser, previous: dict | None) -> dict:
    known = previous if isinstance(previous, dict) else {}
    last_run = known.get("last_run")
    if last_run is None and parser.last_run is not None:
        last_run = parser.last_run.isoformat()
    return {
        "store_slug": slug,
        "is_running": True,
        "last_run": last_run,
        "products_found": known.get("products_found", 0),
        "errors": [],
    }


class ParserService:
    def __init__(self, manager: ParserManager | None = None):
        self._manager = manager or parser_manager

    def register(self, parser: BaseParser) -> None:
        self._manager.register(parser)

    def get(self, slug: str) -> BaseParser | None:
        return self._manager.get(slug)

    def list_parsers(self) -> list[BaseParser]:
        return self._manager.get_all()

    async def get_statuses(self) -> list[dict]:
        statuses = []
        for parser in self._manager.get_all():
            stored = await RedisCache.get(_status_key(parser.store_slug))
            if stored is None:
                stored = {
                    "store_slug": parser.store_slug,
                    "is_running": False,
                    "last_run": parser.last_run.isoformat() if parser.last_run else None,
                    "products_found": 0,
                    "errors": parser.errors,
                }
            statuses.append(stored)
        return statuses

    @staticmethod
    async def _resolve_store_id(db: AsyncSession, slug: str) -> int:
        store = (await db.execute(select(Store).where(Store.slug == slug))).scalar_one_or_none()
        if store is None:
            raise ParserError(f"store '{slug}' not found")
        return store.id

    @staticmethod
    async def _active_offer_count(db: AsyncSession, store_id: int) -> int:
        return (
            await db.execute(
                select(func.count())
                .select_from(StoreOffer)
                .where(
                    StoreOffer.store_id == store_id,
                    StoreOffer.is_active.is_(True),
                )
            )
        ).scalar_one()

    @staticmethod
    def _validate_result(result: ParseResult) -> None:
        if not result.source_sku or not result.source_sku.strip():
            raise ParserParseError("source_sku is empty")
        if not result.title or not result.title.strip():
            raise ParserParseError(f"offer '{result.source_sku}' has an empty title")
        if not result.url or not result.url.strip():
            raise ParserParseError(f"offer '{result.source_sku}' has an empty url")
        try:
            valid_price = result.price_retail.is_finite() and result.price_retail > 0
        except (ArithmeticError, AttributeError, TypeError):
            valid_price = False
        if not valid_price:
            raise ParserParseError(
                f"offer '{result.source_sku}' has invalid retail price: {result.price_retail}"
            )

    @staticmethod
    async def upsert_offer(db: AsyncSession, store_id: int, result: ParseResult) -> StoreOffer:
        ParserService._validate_result(result)
        existing = (
            await db.execute(
                select(StoreOffer).where(
                    StoreOffer.store_id == store_id,
                    StoreOffer.source_sku == result.source_sku,
                )
            )
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        normalized = normalize_name(result.title)

        if existing is None:
            offer = StoreOffer(
                store_id=store_id,
                source_sku=result.source_sku,
                title=result.title,
                normalized_title=normalized,
                description=result.description,
                image_url=result.image_url,
                price_retail=result.price_retail,
                price_opt=result.price_opt,
                price_old=result.price_old,
                stock_status=result.stock_status,
                stock_qty=result.stock_qty,
                url=result.url,
                raw=result.raw or None,
                is_active=True,
                first_seen_at=now,
                last_seen_at=now,
                price_changed_at=now,
            )
            db.add(offer)
            await db.flush()
            db.add(
                OfferPriceHistory(
                    offer_id=offer.id,
                    price_retail=offer.price_retail,
                    price_opt=offer.price_opt,
                    stock_status=offer.stock_status,
                )
            )
            await db.flush()
            return offer

        price_changed = existing.price_retail != result.price_retail
        existing.title = result.title
        existing.normalized_title = normalized
        existing.description = result.description
        existing.image_url = result.image_url
        existing.price_opt = result.price_opt
        existing.price_old = result.price_old
        existing.stock_status = result.stock_status
        existing.stock_qty = result.stock_qty
        existing.url = result.url
        if result.raw:
            existing.raw = result.raw
        existing.is_active = True
        existing.last_seen_at = now
        if price_changed:
            existing.price_retail = result.price_retail
            existing.price_changed_at = now
            db.add(
                OfferPriceHistory(
                    offer_id=existing.id,
                    price_retail=result.price_retail,
                    price_opt=result.price_opt,
                    stock_status=result.stock_status,
                )
            )
        await db.flush()
        return existing

    @staticmethod
    async def _deactivate_stale_offers(
        db: AsyncSession, store_id: int, run_started_at: datetime
    ) -> int:
        result = await db.execute(
            update(StoreOffer)
            .where(
                StoreOffer.store_id == store_id,
                StoreOffer.is_active.is_(True),
                StoreOffer.last_seen_at < run_started_at,
            )
            .values(is_active=False)
        )
        await db.flush()
        return result.rowcount or 0

    async def run_one(
        self,
        db: AsyncSession,
        slug: str,
        full_sync: bool = False,
        limit: int | None = None,
        section: str | None = None,
    ) -> dict:
        parser = self._manager.get(slug)
        if parser is None:
            raise ParserError(f"parser '{slug}' not found")

        catalog_limit = resolve_catalog_limit(full_sync, limit)

        if not await RedisCache.acquire_lock(_lock_key(slug), resolve_lock_ttl(catalog_limit)):
            return {
                "store_slug": slug,
                "status": "already_running",
                "upserted": 0,
                "limit": catalog_limit,
            }

        upserted = 0
        skipped = 0
        deactivated = 0
        try:
            previous = await RedisCache.get(_status_key(slug))
            await RedisCache.set(
                _status_key(slug),
                _running_status(slug, parser, previous),
                ttl=STATUS_TTL,
            )
            store_id = await self._resolve_store_id(db, slug)
            active_before = await self._active_offer_count(db, store_id)
            parser.reset_errors()
            run_started_at = datetime.now(timezone.utc)

            results = await parser.update_catalog(limit=catalog_limit, section=section)
            for result in results:
                try:
                    await self.upsert_offer(db, store_id, result)
                except ParserParseError as exc:
                    skipped += 1
                    parser.errors.append(str(exc))
                    continue
                upserted += 1

            catalog_coverage = None if active_before == 0 else round(upserted / active_before, 4)
            complete_run = (
                full_sync
                and catalog_limit is None
                and not section
                and upserted > 0
                and not parser.errors
                and (catalog_coverage is None or catalog_coverage >= MIN_DEACTIVATION_COVERAGE)
            )
            if complete_run:
                deactivated = await self._deactivate_stale_offers(db, store_id, run_started_at)

            if upserted or deactivated:
                from src.modules.products.service.matching_service import MatchingService

                if upserted:
                    await MatchingService.match_all(db, only_unmatched=True)
                else:
                    await MatchingService.recalc_cluster_aggregates(db)

            parser.last_run = datetime.now(timezone.utc)
            await RedisCache.set(
                _status_key(slug),
                {
                    "store_slug": slug,
                    "is_running": False,
                    "last_run": parser.last_run.isoformat(),
                    "products_found": upserted,
                    "errors": parser.errors,
                },
                ttl=STATUS_TTL,
            )
            return {
                "store_slug": slug,
                "status": "done",
                "upserted": upserted,
                "skipped": skipped,
                "deactivated": deactivated,
                "catalog_coverage": catalog_coverage,
                "limit": catalog_limit,
            }
        except Exception as exc:
            await RedisCache.set(
                _status_key(slug),
                {
                    "store_slug": slug,
                    "is_running": False,
                    "last_run": parser.last_run.isoformat() if parser.last_run else None,
                    "products_found": upserted,
                    "errors": [str(exc)],
                },
                ttl=STATUS_TTL,
            )
            raise
        finally:
            await RedisCache.release_lock(_lock_key(slug))

    async def run_isolated(
        self,
        slug: str,
        full_sync: bool = False,
        limit: int | None = None,
        section: str | None = None,
    ) -> dict:
        async with async_session_factory() as session:
            try:
                result = await self.run_one(
                    session, slug, full_sync=full_sync, limit=limit, section=section
                )
                await session.commit()
                return result
            except Exception as exc:
                await session.rollback()
                return {"store_slug": slug, "status": "error", "error": str(exc)}

    async def run_all(self, full_sync: bool = False, limit: int | None = None) -> list[dict]:
        slugs = [parser.store_slug for parser in self._manager.get_all()]
        return list(
            await asyncio.gather(*(self.run_isolated(slug, full_sync, limit) for slug in slugs))
        )

    async def enqueue_run(
        self,
        slug: str,
        full_sync: bool = False,
        limit: int | None = None,
        section: str | None = None,
    ) -> dict:
        parser = self._manager.get(slug)
        if parser is None:
            raise ParserError(f"parser '{slug}' not found")

        catalog_limit = resolve_catalog_limit(full_sync, limit)
        previous = await RedisCache.get(_status_key(slug))
        queued = isinstance(previous, dict) and previous.get("is_running") is True

        if queued or await RedisCache.exists(_lock_key(slug)):
            return {
                "store_slug": slug,
                "status": "already_running",
                "job_id": None,
                "limit": catalog_limit,
            }

        job_id = await enqueue_parser_run(slug, full_sync, limit, section)

        await RedisCache.set(
            _status_key(slug),
            _running_status(slug, parser, previous),
            ttl=QUEUED_STATUS_TTL,
        )
        return {
            "store_slug": slug,
            "status": "queued",
            "job_id": job_id,
            "limit": catalog_limit,
            "section": section,
        }


parser_service = ParserService()
