import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory
from src.modules.cache import RedisCache
from src.modules.parser.service.base import BaseParser, ParseResult, ParserManager, parser_manager
from src.modules.parser.service.exceptions import ParserError
from src.modules.parser.service.utils import normalize_name
from src.modules.products.model.product import OfferPriceHistory, StoreOffer
from src.modules.stores.model.store import Store

STATUS_TTL = 86400
LOCK_TTL = 3600
FULL_SYNC_LOCK_TTL = 6 * 3600
DEFAULT_RUN_LIMIT = 500


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
    async def upsert_offer(db: AsyncSession, store_id: int, result: ParseResult) -> StoreOffer:
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

    async def run_one(
        self,
        db: AsyncSession,
        slug: str,
        full_sync: bool = False,
        limit: int | None = None,
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
        try:
            await RedisCache.set(
                _status_key(slug),
                {
                    "store_slug": slug,
                    "is_running": True,
                    "last_run": parser.last_run.isoformat() if parser.last_run else None,
                    "products_found": 0,
                    "errors": [],
                },
                ttl=STATUS_TTL,
            )
            store_id = await self._resolve_store_id(db, slug)
            parser.reset_errors()

            results = await parser.update_catalog(limit=catalog_limit)
            for result in results:
                await self.upsert_offer(db, store_id, result)
                upserted += 1

            if upserted:
                from src.modules.products.service.matching_service import MatchingService

                await MatchingService.match_all(db, only_unmatched=True)

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

    async def _run_isolated(self, slug: str, full_sync: bool, limit: int | None) -> dict:
        async with async_session_factory() as session:
            try:
                result = await self.run_one(session, slug, full_sync=full_sync, limit=limit)
                await session.commit()
                return result
            except Exception as exc:
                await session.rollback()
                return {"store_slug": slug, "status": "error", "error": str(exc)}

    async def run_all(self, full_sync: bool = False, limit: int | None = None) -> list[dict]:
        slugs = [parser.store_slug for parser in self._manager.get_all()]
        return list(
            await asyncio.gather(*(self._run_isolated(slug, full_sync, limit) for slug in slugs))
        )


parser_service = ParserService()
