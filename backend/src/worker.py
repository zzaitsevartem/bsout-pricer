import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import delete, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.celery_app import celery_app
from src.config import settings
from src.database import async_session_factory
from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.model.user import Subscription
from src.modules.auth.service.password_service import deliver_mail
from src.modules.broadcast.service.broadcast_service import BroadcastService
from src.modules.parser.service.parser_service import FULL_SYNC_LOCK_TTL, parser_service
from src.modules.parser.service.parsers import register_default_parsers
from src.modules.tracking.service.alert_service import AlertService
from src.modules.tracking.service.price_refresh import refresh_tracked_offers
from src.modules.tracking.service.retention import run_retention

logger = logging.getLogger(__name__)

register_default_parsers()


@celery_app.task(
    name="run_parser",
    time_limit=FULL_SYNC_LOCK_TTL,
    soft_time_limit=FULL_SYNC_LOCK_TTL - 60,
)
def run_parser(
    store_slug: str,
    full_sync: bool = False,
    limit: int | None = None,
    section: str | None = None,
) -> dict:
    return asyncio.run(
        parser_service.run_isolated(store_slug, full_sync=full_sync, limit=limit, section=section)
    )


async def _sync_catalog() -> dict:
    if not settings.parser_full_sync_enabled:
        result = {"status": "disabled", "stores": []}
        logger.info("sync_catalog: %s", result)
        return result

    stores = await parser_service.run_all(full_sync=True)
    result = {"status": "done", "stores": stores}
    logger.info("sync_catalog: %s", result)
    return result


@celery_app.task(name="sync_catalog", time_limit=FULL_SYNC_LOCK_TTL)
def sync_catalog() -> dict:
    return asyncio.run(_sync_catalog())


async def _sync_prices() -> dict:
    async with async_session_factory() as db:
        stats = await refresh_tracked_offers(db)
        notifications = await AlertService.scan_for_drops(db)
        await db.commit()
    stats["notifications"] = len(notifications)
    logger.info("sync_prices: %s", stats)
    return stats


@celery_app.task(name="sync_prices")
def sync_prices() -> dict:
    return asyncio.run(_sync_prices())


async def _expire_subscriptions_impl(db: AsyncSession) -> dict:
    result = await db.execute(
        update(Subscription)
        .where(
            Subscription.is_active.is_(True),
            Subscription.end_date < datetime.now(timezone.utc),
        )
        .values(is_active=False)
    )
    await db.commit()
    return {"expired": result.rowcount or 0}


async def _expire_subscriptions(db: AsyncSession | None = None) -> dict:
    if db is not None:
        return await _expire_subscriptions_impl(db)
    async with async_session_factory() as session:
        return await _expire_subscriptions_impl(session)


@celery_app.task(name="expire_subscriptions")
def expire_subscriptions() -> dict:
    return asyncio.run(_expire_subscriptions())


async def _cleanup_refresh_tokens_impl(db: AsyncSession) -> dict:
    result = await db.execute(
        delete(RefreshToken).where(
            or_(
                RefreshToken.expires_at < datetime.now(timezone.utc),
                RefreshToken.revoked_at.isnot(None),
            )
        )
    )
    await db.commit()
    return {"deleted": result.rowcount or 0}


async def _cleanup_refresh_tokens(db: AsyncSession | None = None) -> dict:
    if db is not None:
        return await _cleanup_refresh_tokens_impl(db)
    async with async_session_factory() as session:
        return await _cleanup_refresh_tokens_impl(session)


@celery_app.task(name="cleanup_refresh_tokens")
def cleanup_refresh_tokens() -> dict:
    return asyncio.run(_cleanup_refresh_tokens())


async def _prune_history(db: AsyncSession | None = None) -> dict:
    if db is not None:
        return await run_retention(db)
    async with async_session_factory() as session:
        return await run_retention(session)


@celery_app.task(name="prune_history", time_limit=3600, soft_time_limit=3540)
def prune_history() -> dict:
    return asyncio.run(_prune_history())


async def _send_password_mail(to: str, subject: str, text: str, html: str | None = None) -> None:
    await deliver_mail(to, subject, text, html)


@celery_app.task(name="send_password_mail")
def send_password_mail(to: str, subject: str, text: str, html: str | None = None) -> None:
    asyncio.run(_send_password_mail(to, subject, text, html))


async def _send_broadcast(broadcast_id: int) -> dict:
    return await BroadcastService.run_broadcast_job(broadcast_id)


@celery_app.task(name="send_broadcast")
def send_broadcast(broadcast_id: int) -> dict:
    return asyncio.run(_send_broadcast(broadcast_id))
