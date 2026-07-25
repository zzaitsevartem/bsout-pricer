import json
from typing import Any

import redis.asyncio as aioredis

from src.config import settings

_cache: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _cache
    if _cache is None:
        _cache = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _cache


async def close_redis() -> None:
    global _cache
    if _cache is not None:
        await _cache.aclose()
        _cache = None


class RedisCache:
    @staticmethod
    async def get(key: str) -> Any | None:
        r = get_redis()
        val = await r.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val

    @staticmethod
    async def set(key: str, value: Any, ttl: int = 300) -> None:
        r = get_redis()
        data = json.dumps(value, default=str)
        await r.set(key, data, ex=ttl)

    @staticmethod
    async def delete(key: str) -> None:
        r = get_redis()
        await r.delete(key)

    @staticmethod
    async def exists(key: str) -> bool:
        r = get_redis()
        return await r.exists(key) > 0

    @staticmethod
    async def expire(key: str, ttl: int) -> None:
        r = get_redis()
        await r.expire(key, ttl)

    @staticmethod
    async def acquire_lock(key: str, ttl: int = 3600) -> bool:
        r = get_redis()
        acquired = await r.set(key, "1", nx=True, ex=ttl)
        return bool(acquired)

    @staticmethod
    async def release_lock(key: str) -> None:
        r = get_redis()
        await r.delete(key)
