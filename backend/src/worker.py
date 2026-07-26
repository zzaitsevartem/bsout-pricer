import logging
from datetime import datetime, timezone

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import delete, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import async_session_factory
from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.model.user import Subscription
from src.modules.parser.service.parser_service import parser_service
from src.modules.parser.service.parsers import register_default_parsers
from src.modules.tracking.service.alert_service import AlertService
from src.modules.tracking.service.price_refresh import refresh_tracked_offers

logger = logging.getLogger(__name__)


async def startup(ctx) -> None:
    register_default_parsers()


async def sync_catalog(ctx) -> list[dict]:
    return await parser_service.run_all()


async def sync_prices(ctx) -> dict:
    async with async_session_factory() as db:
        stats = await refresh_tracked_offers(db)
        notifications = await AlertService.scan_for_drops(db)
        await db.commit()
    stats["notifications"] = len(notifications)
    logger.info("sync_prices: %s", stats)
    return stats


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


class WorkerSettings:
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port)
    on_startup = startup
    functions = [sync_catalog, sync_prices, expire_subscriptions, cleanup_refresh_tokens]
    cron_jobs = [
        cron(sync_catalog, hour=3, minute=0),
        cron(sync_prices, hour={7, 13, 19}, minute=30),
        cron(expire_subscriptions, minute=5),
        cron(cleanup_refresh_tokens, hour=4, minute=30),
    ]
