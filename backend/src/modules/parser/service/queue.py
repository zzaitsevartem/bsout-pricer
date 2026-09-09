import asyncio

from src.config import settings

PARSER_QUEUE_JOB = "run_parser"

_pool = None
_pool_lock = asyncio.Lock()


async def get_parser_pool():
    global _pool
    if _pool is not None:
        return _pool
    async with _pool_lock:
        if _pool is None:
            from arq import create_pool
            from arq.connections import RedisSettings

            _pool = await create_pool(
                RedisSettings(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                )
            )
    return _pool


async def close_parser_queue() -> None:
    global _pool
    pool = _pool
    _pool = None
    if pool is not None:
        await pool.close()


async def enqueue_parser_run(
    store_slug: str,
    full_sync: bool,
    limit: int | None,
    section: str | None = None,
) -> str | None:
    pool = await get_parser_pool()
    job = await pool.enqueue_job(PARSER_QUEUE_JOB, store_slug, full_sync, limit, section)
    return job.job_id if job is not None else None
