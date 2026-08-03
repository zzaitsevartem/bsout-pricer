from datetime import datetime, timezone

from src.modules.cache.service.redis_cache import RedisCache

TRIAL_KEY_PREFIX = "trial:search"
TRIAL_TTL_SECONDS = 60 * 60 * 24 * 30

_fallback_store: dict[str, dict] = {}


class TrialService:

    @staticmethod
    async def is_used(client_id: str) -> bool:
        key = f"{TRIAL_KEY_PREFIX}:{client_id}"
        try:
            return await RedisCache.exists(key)
        except Exception:
            return client_id in _fallback_store

    @staticmethod
    async def mark_used(client_id: str, query: str = "") -> None:
        key = f"{TRIAL_KEY_PREFIX}:{client_id}"
        record = {
            "used": True,
            "used_at": datetime.now(timezone.utc).isoformat(),
            "query": query,
        }
        try:
            await RedisCache.set(key, record, ttl=TRIAL_TTL_SECONDS)
        except Exception:
            _fallback_store[client_id] = record
