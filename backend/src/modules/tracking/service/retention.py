import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _positive_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


PRICE_HISTORY_RETENTION_DAYS = _positive_int_env("RETENTION_PRICE_HISTORY_DAYS", 365)
PRICE_HISTORY_DOWNSAMPLE_AFTER_DAYS = _positive_int_env(
    "RETENTION_PRICE_HISTORY_DOWNSAMPLE_AFTER_DAYS", 180
)
SEARCH_HISTORY_RETENTION_DAYS = _positive_int_env("RETENTION_SEARCH_HISTORY_DAYS", 90)
RETENTION_BATCH_SIZE = _positive_int_env("RETENTION_BATCH_SIZE", 5000)
RETENTION_MAX_BATCHES = _positive_int_env("RETENTION_MAX_BATCHES", 1000)


_DOWNSAMPLE_PRICE_HISTORY = text(
    """
    WITH ranked AS (
        SELECT
            id,
            row_number() OVER (
                PARTITION BY offer_id, date(timezone('UTC', recorded_at))
                ORDER BY price_retail ASC, id ASC
            ) AS rn
        FROM offer_price_history
        WHERE recorded_at < :downsample_before
          AND recorded_at >= :delete_before
    )
    DELETE FROM offer_price_history
    WHERE id IN (SELECT id FROM ranked WHERE rn > 1 ORDER BY id LIMIT :batch_size)
    """
)


_PURGE_PRICE_HISTORY = text(
    """
    WITH stale AS (
        SELECT id, offer_id, recorded_at
        FROM offer_price_history
        WHERE recorded_at < :delete_before
    ),
    fresh_offers AS (
        SELECT DISTINCT offer_id
        FROM offer_price_history
        WHERE recorded_at >= :delete_before
    ),
    ranked AS (
        SELECT
            s.id,
            row_number() OVER (
                PARTITION BY s.offer_id ORDER BY s.recorded_at DESC, s.id DESC
            ) AS rn,
            (f.offer_id IS NOT NULL) AS has_fresh
        FROM stale s
        LEFT JOIN fresh_offers f ON f.offer_id = s.offer_id
    )
    DELETE FROM offer_price_history
    WHERE id IN (
        SELECT id FROM ranked WHERE rn > 1 OR has_fresh ORDER BY id LIMIT :batch_size
    )
    """
)


_PURGE_SEARCH_HISTORY = text(
    """
    DELETE FROM search_history
    WHERE id IN (
        SELECT id FROM search_history
        WHERE created_at < :delete_before
        ORDER BY id
        LIMIT :batch_size
    )
    """
)


async def _run_batched(
    db: AsyncSession,
    statement,
    params: dict,
    batch_size: int,
    max_batches: int,
) -> dict:
    deleted = 0
    batches = 0
    largest_batch = 0

    while batches < max_batches:
        result = await db.execute(statement, {**params, "batch_size": batch_size})
        await db.commit()
        rowcount = result.rowcount or 0
        deleted += rowcount
        batches += 1
        largest_batch = max(largest_batch, rowcount)
        if rowcount < batch_size:
            break

    return {"deleted": deleted, "batches": batches, "largest_batch": largest_batch}


async def purge_price_history(
    db: AsyncSession,
    retention_days: int = PRICE_HISTORY_RETENTION_DAYS,
    downsample_after_days: int = PRICE_HISTORY_DOWNSAMPLE_AFTER_DAYS,
    batch_size: int = RETENTION_BATCH_SIZE,
    max_batches: int = RETENTION_MAX_BATCHES,
    now: datetime | None = None,
) -> dict:
    moment = now or datetime.now(timezone.utc)
    delete_before = moment - timedelta(days=retention_days)
    downsample_before = moment - timedelta(days=downsample_after_days)

    downsampled = await _run_batched(
        db,
        _DOWNSAMPLE_PRICE_HISTORY,
        {"downsample_before": downsample_before, "delete_before": delete_before},
        batch_size,
        max_batches,
    )
    purged = await _run_batched(
        db,
        _PURGE_PRICE_HISTORY,
        {"delete_before": delete_before},
        batch_size,
        max_batches,
    )

    return {
        "downsampled": downsampled["deleted"],
        "downsample_batches": downsampled["batches"],
        "purged": purged["deleted"],
        "purge_batches": purged["batches"],
        "largest_batch": max(downsampled["largest_batch"], purged["largest_batch"]),
        "delete_before": delete_before.isoformat(),
        "downsample_before": downsample_before.isoformat(),
    }


async def purge_search_history(
    db: AsyncSession,
    retention_days: int = SEARCH_HISTORY_RETENTION_DAYS,
    batch_size: int = RETENTION_BATCH_SIZE,
    max_batches: int = RETENTION_MAX_BATCHES,
    now: datetime | None = None,
) -> dict:
    moment = now or datetime.now(timezone.utc)
    delete_before = moment - timedelta(days=retention_days)

    purged = await _run_batched(
        db,
        _PURGE_SEARCH_HISTORY,
        {"delete_before": delete_before},
        batch_size,
        max_batches,
    )

    return {
        "purged": purged["deleted"],
        "purge_batches": purged["batches"],
        "largest_batch": purged["largest_batch"],
        "delete_before": delete_before.isoformat(),
    }


async def run_retention(
    db: AsyncSession,
    price_history_retention_days: int = PRICE_HISTORY_RETENTION_DAYS,
    price_history_downsample_after_days: int = PRICE_HISTORY_DOWNSAMPLE_AFTER_DAYS,
    search_history_retention_days: int = SEARCH_HISTORY_RETENTION_DAYS,
    batch_size: int = RETENTION_BATCH_SIZE,
    max_batches: int = RETENTION_MAX_BATCHES,
    now: datetime | None = None,
) -> dict:
    price_history = await purge_price_history(
        db,
        retention_days=price_history_retention_days,
        downsample_after_days=price_history_downsample_after_days,
        batch_size=batch_size,
        max_batches=max_batches,
        now=now,
    )
    search_history = await purge_search_history(
        db,
        retention_days=search_history_retention_days,
        batch_size=batch_size,
        max_batches=max_batches,
        now=now,
    )

    stats = {"price_history": price_history, "search_history": search_history}
    logger.info("retention: %s", stats)
    return stats
