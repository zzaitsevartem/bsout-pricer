from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.export.service.csv_writer import (
    bool_cell,
    datetime_cell,
    int_cell,
    join_cell,
    money_cell,
    number_cell,
    text_cell,
)
from src.modules.products.service.comparison_service import ComparisonService
from src.modules.stores.model.store import Store
from src.modules.tracking.service.tracking_service import TrackingService

CATALOG_HEADER = [
    "Канонический товар",
    "Бренд",
    "Устройство",
    "Тип детали",
    "Класс качества",
    "Мин. розница, ₽",
    "Мин. опт, ₽",
    "Магазинов",
    "Предложений",
    "Магазины",
]

TRACKING_HEADER = [
    "Товар",
    "Текущая цена, ₽",
    "Целевая цена, ₽",
    "Изменение, ₽",
    "Изменение, %",
    "Магазинов",
    "Цель достигнута",
    "Отслеживание активно",
    "Добавлено",
]

BATCH_SIZE = 500


class ExportService:
    @staticmethod
    async def store_names(db: AsyncSession) -> dict[str, str]:
        rows = (await db.execute(select(Store.slug, Store.name))).all()
        return {row.slug: row.name for row in rows}

    @staticmethod
    async def catalog_total(
        db: AsyncSession,
        query: str = "",
        device_id: int | None = None,
        part_type_id: int | None = None,
        quality_tier_id: int | None = None,
    ) -> int:
        _, total = await ComparisonService.search_catalog(
            db=db,
            query=query,
            device_id=device_id,
            part_type_id=part_type_id,
            quality_tier_id=quality_tier_id,
            page=1,
            per_page=1,
        )
        return total

    @staticmethod
    def catalog_row(item: dict, store_names: dict[str, str]) -> list[str]:
        brand = item.get("brand") or {}
        device = item.get("device") or {}
        part_type = item.get("part_type") or {}
        quality_tier = item.get("quality_tier") or {}
        slugs = item.get("store_slugs") or []
        return [
            text_cell(item.get("canonical_name")),
            text_cell(brand.get("name")),
            text_cell(device.get("name")),
            text_cell(part_type.get("name_ru")),
            text_cell(quality_tier.get("name_ru")),
            money_cell(item.get("min_price_retail")),
            money_cell(item.get("min_price_opt")),
            int_cell(item.get("stores_count")),
            int_cell(item.get("offers_count")),
            join_cell(store_names.get(slug, slug) for slug in slugs),
        ]

    @staticmethod
    async def iter_catalog_rows(
        db: AsyncSession,
        limit: int,
        query: str = "",
        device_id: int | None = None,
        part_type_id: int | None = None,
        quality_tier_id: int | None = None,
        sort_by: str = "min_price_asc",
    ) -> AsyncIterator[list[str]]:
        store_names = await ExportService.store_names(db)
        emitted = 0
        page = 1

        while emitted < limit:
            results, _ = await ComparisonService.search_catalog(
                db=db,
                query=query,
                device_id=device_id,
                part_type_id=part_type_id,
                quality_tier_id=quality_tier_id,
                sort_by=sort_by,
                page=page,
                per_page=BATCH_SIZE,
            )
            if not results:
                return

            for item in results:
                yield ExportService.catalog_row(item, store_names)
                emitted += 1
                if emitted >= limit:
                    return

            if len(results) < BATCH_SIZE:
                return
            page += 1

    @staticmethod
    async def collect_catalog_rows(
        db: AsyncSession,
        limit: int,
        query: str = "",
        device_id: int | None = None,
        part_type_id: int | None = None,
        quality_tier_id: int | None = None,
        sort_by: str = "min_price_asc",
    ) -> list[list[str]]:
        return [
            row
            async for row in ExportService.iter_catalog_rows(
                db=db,
                limit=limit,
                query=query,
                device_id=device_id,
                part_type_id=part_type_id,
                quality_tier_id=quality_tier_id,
                sort_by=sort_by,
            )
        ]

    @staticmethod
    async def tracking_total(db: AsyncSession, user_id: int, is_active: bool | None = None) -> int:
        _, total = await TrackingService.list_for_user(
            db=db, user_id=user_id, is_active=is_active, page=1, per_page=1
        )
        return total

    @staticmethod
    def tracking_row(item: dict) -> list[str]:
        return [
            text_cell(item.get("canonical_name")),
            money_cell(item.get("current_price")),
            money_cell(item.get("target_price")),
            money_cell(item.get("price_delta")),
            number_cell(item.get("price_delta_pct")),
            int_cell(item.get("stores_count")),
            bool_cell(item.get("target_reached")),
            bool_cell(item.get("is_active")),
            datetime_cell(item.get("created_at")),
        ]

    @staticmethod
    async def iter_tracking_rows(
        db: AsyncSession,
        user_id: int,
        limit: int,
        is_active: bool | None = None,
    ) -> AsyncIterator[list[str]]:
        emitted = 0
        page = 1

        while emitted < limit:
            results, _ = await TrackingService.list_for_user(
                db=db,
                user_id=user_id,
                is_active=is_active,
                page=page,
                per_page=BATCH_SIZE,
            )
            if not results:
                return

            for item in results:
                yield ExportService.tracking_row(item)
                emitted += 1
                if emitted >= limit:
                    return

            if len(results) < BATCH_SIZE:
                return
            page += 1
