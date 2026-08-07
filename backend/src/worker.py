import logging
from datetime import datetime, timezone

from arq import cron, func
from arq.connections import RedisSettings
from sqlalchemy import delete, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import async_session_factory
from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.model.user import Subscription
from src.modules.auth.service.password_service import deliver_mail
from src.modules.parser.service.parser_service import FULL_SYNC_LOCK_TTL, parser_service
from src.modules.parser.service.parsers import register_default_parsers
from src.modules.parser.service.queue import PARSER_QUEUE_JOB
from src.modules.tracking.service.alert_service import AlertService
from src.modules.tracking.service.price_refresh import refresh_tracked_offers
from src.modules.tracking.service.retention import run_retention

logger = logging.getLogger(__name__)


async def startup(ctx) -> None:
    register_default_parsers()


async def sync_catalog(ctx) -> dict:
    if not settings.parser_full_sync_enabled:
        result = {"status": "disabled", "stores": []}
        logger.info("sync_catalog: %s", result)
        return result

    stores = await parser_service.run_all(full_sync=True)
    result = {"status": "done", "stores": stores}
    logger.info("sync_catalog: %s", result)
    return result


async def run_parser(
    ctx,
    store_slug: str,
    full_sync: bool = False,
    limit: int | None = None,
    section: str | None = None,
) -> dict:
    result = await parser_service.run_isolated(
        store_slug, full_sync=full_sync, limit=limit, section=section
    )
    logger.info("run_parser: %s", result)
    return result


async def sync_prices(ctx) -> dict:
    async with async_session_factory() as db:
        stats = await refresh_tracked_offers(db)
        notifications = await AlertService.scan_for_drops(db)
        await db.commit()
    stats["notifications"] = len(notifications)
    logger.info("sync_prices: %s", stats)
    return stats


async def send_password_mail(
    ctx,
    to: str,
    subject: str,
    text: str,
    html: str | None = None,
) -> dict:
    await deliver_mail(to, subject, text, html)
    return {"delivered": True}


async def _expire_subscriptions(db: AsyncSession) -> dict:
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


async def expire_subscriptions(ctx, db: AsyncSession | None = None) -> dict:
    if db is not None:
        return await _expire_subscriptions(db)
    async with async_session_factory() as session:
        return await _expire_subscriptions(session)


async def _cleanup_refresh_tokens(db: AsyncSession) -> dict:
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


async def cleanup_refresh_tokens(ctx, db: AsyncSession | None = None) -> dict:
    if db is not None:
        return await _cleanup_refresh_tokens(db)
    async with async_session_factory() as session:
        return await _cleanup_refresh_tokens(session)


async def _prune_history(db: AsyncSession) -> dict:
    return await run_retention(db)


async def prune_history(ctx, db: AsyncSession | None = None) -> dict:
    if db is not None:
        return await _prune_history(db)
    async with async_session_factory() as session:
        return await _prune_history(session)


class WorkerSettings:
    redis_settings = RedisSettings(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
    )
    on_startup = startup
    functions = [
        func(run_parser, name=PARSER_QUEUE_JOB, timeout=FULL_SYNC_LOCK_TTL),
        sync_catalog,
        sync_prices,
        expire_subscriptions,
        cleanup_refresh_tokens,
        send_password_mail,
        prune_history,
    ]
    cron_jobs = [
        cron(sync_catalog, hour=3, minute=0),
        cron(sync_prices, hour={7, 13, 19}, minute=30),
        cron(expire_subscriptions, minute=5),
        cron(cleanup_refresh_tokens, hour=4, minute=30),
        cron(prune_history, weekday="sun", hour=4, minute=45, timeout=3600),
    ]
