import logging
import time
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.config import settings
from src.modules.cache.service.redis_cache import get_redis

logger = logging.getLogger(__name__)

DEFAULT_NAMESPACE = "ratelimit"
DEFAULT_AUTH_MAX_REQUESTS = 10
DEFAULT_AUTH_WINDOW = 300
DEFAULT_AUTH_PATHS = (
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/api/auth/password-reset/request",
    "/api/auth/password-reset/confirm",
    "/api/auth/password/change",
)
REDIS_ERRORS = (RedisError, OSError)
THROTTLED_DETAIL = "Too many requests. Try again later."


class _ResettableCounters(dict):
    def __init__(self, owner: "RateLimitMiddleware") -> None:
        super().__init__()
        self._owner = owner

    def clear(self) -> None:
        super().clear()
        self._owner.rotate_namespace()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        max_requests: int = 60,
        window: int = 60,
        trust_forwarded_for: bool = False,
        auth_max_requests: int | None = None,
        auth_window: int | None = None,
        auth_paths: tuple[str, ...] | None = None,
        namespace: str = DEFAULT_NAMESPACE,
        redis_factory=None,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.trust_forwarded_for = trust_forwarded_for
        self.auth_max_requests = int(
            auth_max_requests
            if auth_max_requests is not None
            else getattr(settings, "auth_rate_limit_max_requests", DEFAULT_AUTH_MAX_REQUESTS)
        )
        self.auth_window = int(
            auth_window
            if auth_window is not None
            else getattr(settings, "auth_rate_limit_window", DEFAULT_AUTH_WINDOW)
        )
        self.auth_paths = tuple(
            auth_paths if auth_paths is not None else DEFAULT_AUTH_PATHS,
        )
        self.namespace = namespace
        self.redis_factory = redis_factory if redis_factory is not None else get_redis
        self._requests = _ResettableCounters(self)
        self._since_sweep = 0

    def rotate_namespace(self) -> str:
        self.namespace = f"{DEFAULT_NAMESPACE}:{uuid4().hex}"
        return self.namespace

    def _client_key(self, request: Request) -> str:
        if self.trust_forwarded_for:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                first = forwarded.split(",")[0].strip()
                if first:
                    return first
        return request.client.host if request.client else "unknown"

    def _is_auth_path(self, request: Request) -> bool:
        path = getattr(getattr(request, "url", None), "path", "") or ""
        normalized = path.rstrip("/") or "/"
        return any(normalized == candidate.rstrip("/") for candidate in self.auth_paths)

    def _buckets(self, request: Request) -> list[tuple[str, int, int]]:
        buckets = [("global", self.max_requests, self.window)]
        if self._is_auth_path(request):
            buckets.insert(0, ("auth", self.auth_max_requests, self.auth_window))
        return buckets

    async def _consume(self, redis, key: str, limit: int, window: int, now: float) -> bool:
        member = f"{now:.6f}-{uuid4().hex}"
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zadd(key, {member: now})
        pipe.zcard(key)
        pipe.expire(key, int(window) + 1)
        results = await pipe.execute()
        if int(results[2]) <= limit:
            return True
        await redis.zrem(key, member)
        return False

    async def _retry_after(self, redis, key: str, window: int, now: float) -> int:
        oldest = await redis.zrange(key, 0, 0, withscores=True)
        if not oldest:
            return max(1, int(window))
        return max(1, int(float(oldest[0][1]) + window - now) + 1)

    def _throttled(self, limit: int, retry_after: int) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": THROTTLED_DETAIL},
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(max(0, limit)),
                "X-RateLimit-Remaining": "0",
            },
        )

    async def _evaluate(self, request: Request) -> JSONResponse | None:
        buckets = self._buckets(request)
        for _, limit, window in buckets:
            if limit <= 0:
                return self._throttled(limit, max(1, int(window)))

        client_key = self._client_key(request)
        now = time.time()
        try:
            redis = self.redis_factory()
            for scope, limit, window in buckets:
                key = f"{self.namespace}:{scope}:{client_key}"
                if not await self._consume(redis, key, limit, window, now):
                    return self._throttled(limit, await self._retry_after(redis, key, window, now))
        except REDIS_ERRORS as exc:
            logger.warning("rate limit not enforced, redis unavailable: %s", exc)
        return None

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        throttled = await self._evaluate(request)
        if throttled is not None:
            return throttled
        return await call_next(request)
