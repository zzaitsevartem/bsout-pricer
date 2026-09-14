from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.admin.schema.offer_import import (
    OfferImportItem,
    OfferImportResponse,
    OfferImportRowError,
)
from src.modules.parser.service.base import ParseResult
from src.modules.parser.service.parser_service import ParserService
from src.modules.products.model.product import StoreOffer
from src.modules.products.service.matching_service import MatchingService
from src.modules.stores.model.store import Store

MAX_REASON_LENGTH = 300


def _format_validation_error(exc: ValidationError) -> str:
    parts = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error["loc"]) or "body"
        parts.append(f"{location}: {error['msg']}")
    return "; ".join(parts) or "invalid row"


def _format_exception(exc: Exception) -> str:
    text = str(exc).strip().split("\n")[0] or exc.__class__.__name__
    return text[:MAX_REASON_LENGTH]


class OfferImportService:
    @staticmethod
    def _to_parse_result(item: OfferImportItem) -> ParseResult:
        return ParseResult(
            source_sku=item.source_sku,
            title=item.title,
            price_retail=item.price_retail,
            price_opt=item.price_opt,
            price_old=item.price_old,
            description=item.description,
            image_url=item.image_url,
            category=item.category,
            stock_status=item.stock_status,
            stock_qty=item.stock_qty,
            url=item.url,
            raw=item.model_dump(mode="json"),
        )

    @staticmethod
    async def _store_ids_by_slug(db: AsyncSession) -> dict[str, int]:
        rows = await db.execute(select(Store.slug, Store.id))
        return {slug: store_id for slug, store_id in rows.all()}

    @staticmethod
    async def _offer_exists(db: AsyncSession, store_id: int, source_sku: str) -> bool:
        found = await db.execute(
            select(StoreOffer.id).where(
                StoreOffer.store_id == store_id,
                StoreOffer.source_sku == source_sku,
            )
        )
        return found.scalar_one_or_none() is not None

    @classmethod
    async def import_offers(cls, db: AsyncSession, rows: list[Any]) -> OfferImportResponse:
        store_ids = await cls._store_ids_by_slug(db)
        created = 0
        updated = 0
        errors: list[OfferImportRowError] = []

        for index, row in enumerate(rows):
            try:
                item = OfferImportItem.model_validate(row)
            except ValidationError as exc:
                errors.append(
                    OfferImportRowError(index=index, reason=_format_validation_error(exc))
                )
                continue

            store_id = store_ids.get(item.store_slug)
            if store_id is None:
                errors.append(
                    OfferImportRowError(
                        index=index,
                        reason=f"store '{item.store_slug}' not found",
                        store_slug=item.store_slug,
                        source_sku=item.source_sku,
                    )
                )
                continue

            try:
                existed = await cls._offer_exists(db, store_id, item.source_sku)
                async with db.begin_nested():
                    await ParserService.upsert_offer(db, store_id, cls._to_parse_result(item))
            except Exception as exc:
                errors.append(
                    OfferImportRowError(
                        index=index,
                        reason=_format_exception(exc),
                        store_slug=item.store_slug,
                        source_sku=item.source_sku,
                    )
                )
                continue

            if existed:
                updated += 1
            else:
                created += 1

        if created or updated:
            await MatchingService.match_all(db, only_unmatched=True)

        return OfferImportResponse(
            total=len(rows),
            created=created,
            updated=updated,
            skipped=len(errors),
            errors=errors,
        )
