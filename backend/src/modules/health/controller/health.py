import asyncio
import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from src.database import async_session_factory
from src.modules.cache.service.redis_cache import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

PROBE_TIMEOUT_SECONDS = 2.0


async def _check_postgres() -> None:
    async with async_session_factory() as session:
        await session.execute(text("SELECT 1"))


async def _check_redis() -> None:
    await get_redis().ping()


async def _probe(name: str, coro_factory) -> bool:
    try:
        await asyncio.wait_for(coro_factory(), timeout=PROBE_TIMEOUT_SECONDS)
    except Exception as exc:
        logger.warning("readiness probe failed for %s: %s", name, type(exc).__name__)
        return False
    return True


@router.get("/api/health")
async def health():
    return {"status": "ok"}


@router.get("/api/health/live")
async def health_live():
    return {"status": "ok"}


@router.get("/api/health/ready")
async def health_ready(response: Response):
    postgres_ok, redis_ok = await asyncio.gather(
        _probe("postgres", _check_postgres),
        _probe("redis", _check_redis),
    )

    ready = postgres_ok and redis_ok
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if ready else "degraded",
        "postgres": "ok" if postgres_ok else "unavailable",
        "redis": "ok" if redis_ok else "unavailable",
    }
