from arq import cron
from arq.connections import RedisSettings

from src.config import settings
from src.modules.parser.service.parser_service import parser_service


async def sync_catalog(ctx) -> list[dict]:
    return await parser_service.run_all()


async def sync_prices(ctx) -> list[dict]:
    return await parser_service.run_all()


class WorkerSettings:
    redis_settings = RedisSettings(host=settings.redis_host, port=settings.redis_port)
    functions = [sync_catalog, sync_prices]
    cron_jobs = [
        cron(sync_catalog, hour=3, minute=0),
        cron(sync_prices, hour={0, 6, 12, 18}, minute=0),
    ]
