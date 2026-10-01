import logging

import httpx
import pytest
from fastapi import FastAPI
from redis.exceptions import ConnectionError as RedisConnectionError

from src.middleware import rate_limit as rate_limit_module
from src.middleware.rate_limit import (
    DEFAULT_AUTH_MAX_REQUESTS,
    DEFAULT_AUTH_WINDOW,
    RateLimitMiddleware,
)
from src.modules.cache.service.redis_cache import get_redis

pytestmark = pytest.mark.unit


class FakeRedis:
    def __init__(self):
        self.store: dict[str, dict[str, float]] = {}
        self.ttls: dict[str, int] = {}
        self.fail = False

    def _guard(self) -> None:
        if self.fail:
            raise RedisConnectionError("connection refused")

    def pipeline(self, transaction: bool = True) -> "FakePipeline":
        return FakePipeline(self)

    async def zrem(self, key: str, *members: str) -> int:
        self._guard()
        bucket = self.store.get(key, {})
        return sum(1 for member in members if bucket.pop(member, None) is not None)

    async def zrange(self, key: str, start: int, stop: int, withscores: bool = False):
        self._guard()
        items = sorted(self.store.get(key, {}).items(), key=lambda item: item[1])
        sliced = items[start:] if stop == -1 else items[start : stop + 1]
        return sliced if withscores else [member for member, _ in sliced]

    def _apply(self, op: tuple):
        name = op[0]
        if name == "zremrangebyscore":
            _, key, low, high = op
            bucket = self.store.setdefault(key, {})
            doomed = [member for member, score in bucket.items() if low <= score <= high]
            for member in doomed:
                del bucket[member]
            return len(doomed)
        if name == "zadd":
            _, key, mapping = op
            bucket = self.store.setdefault(key, {})
            added = sum(1 for member in mapping if member not in bucket)
            bucket.update(mapping)
            return added
        if name == "zcard":
            return len(self.store.get(op[1], {}))
        if name == "expire":
            self.ttls[op[1]] = op[2]
            return True
        raise AssertionError(f"unsupported redis op {name}")


class FakePipeline:
    def __init__(self, redis: FakeRedis):
        self.redis = redis
        self.ops: list[tuple] = []

    def zremrangebyscore(self, key: str, low: float, high: float) -> "FakePipeline":
        self.ops.append(("zremrangebyscore", key, low, high))
        return self

    def zadd(self, key: str, mapping: dict[str, float]) -> "FakePipeline":
        self.ops.append(("zadd", key, mapping))
        return self

    def zcard(self, key: str) -> "FakePipeline":
        self.ops.append(("zcard", key))
        return self

    def expire(self, key: str, ttl: int) -> "FakePipeline":
        self.ops.append(("expire", key, ttl))
        return self

    async def execute(self) -> list:
        self.redis._guard()
        results = [self.redis._apply(op) for op in self.ops]
        self.ops = []
        return results


class FakeClock:
    def __init__(self, start: float = 1_000_000.0):
        self.now = start

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeClient:
    def __init__(self, host: str):
        self.host = host


class FakeURL:
    def __init__(self, path: str):
        self.path = path


class FakeRequest:
    def __init__(
        self,
        host: str | None = "10.0.0.1",
        path: str = "/api/search",
        headers: dict[str, str] | None = None,
    ):
        self.client = FakeClient(host) if host is not None else None
        self.url = FakeURL(path)
        self.headers = headers or {}


class CallNextSpy:
    def __init__(self):
        self.calls: list[FakeRequest] = []
        self.response = object()

    async def __call__(self, request):
        self.calls.append(request)
        return self.response


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(rate_limit_module, "time", fake)
    return fake


@pytest.fixture
def redis() -> FakeRedis:
    return FakeRedis()


def build_middleware(redis: FakeRedis, **kwargs) -> RateLimitMiddleware:
    kwargs.setdefault("max_requests", 3)
    kwargs.setdefault("window", 60)
    return RateLimitMiddleware(app=None, redis_factory=lambda: redis, **kwargs)


async def test_default_redis_factory_is_the_shared_cache_client():
    assert RateLimitMiddleware(app=None).redis_factory is get_redis


async def test_counters_live_in_redis_and_not_in_process_memory(clock, redis):
    middleware = build_middleware(redis, max_requests=5)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)

    assert middleware._requests == {}
    assert [key for key in redis.store if key.endswith(":global:10.0.0.1")]
    assert sum(len(bucket) for bucket in redis.store.values()) == 1


async def test_two_middleware_instances_share_one_redis_counter(clock, redis):
    worker_one = build_middleware(redis, max_requests=2)
    worker_two = build_middleware(redis, max_requests=2)
    call_next = CallNextSpy()

    await worker_one.dispatch(FakeRequest(), call_next)
    await worker_two.dispatch(FakeRequest(), call_next)

    rejected = await worker_two.dispatch(FakeRequest(), call_next)

    assert rejected.status_code == 429
    assert len(call_next.calls) == 2


async def test_second_instance_sees_the_limit_exhausted_by_the_first(clock, redis):
    worker_one = build_middleware(redis, max_requests=1)
    worker_two = build_middleware(redis, max_requests=1)
    call_next = CallNextSpy()

    await worker_one.dispatch(FakeRequest(), call_next)

    assert (await worker_two.dispatch(FakeRequest(), call_next)).status_code == 429


async def test_redis_keys_get_a_ttl_so_idle_clients_are_evicted(clock, redis):
    middleware = build_middleware(redis, max_requests=5, window=60)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)

    assert set(redis.ttls.values()) == {61}


async def test_rotating_the_namespace_isolates_counters(clock, redis):
    middleware = build_middleware(redis, max_requests=1)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)
    assert (await middleware.dispatch(FakeRequest(), call_next)).status_code == 429

    middleware.rotate_namespace()

    assert await middleware.dispatch(FakeRequest(), call_next) is call_next.response


async def test_clearing_the_legacy_counter_dict_rotates_the_namespace(clock, redis):
    middleware = build_middleware(redis, max_requests=1)
    call_next = CallNextSpy()
    before = middleware.namespace

    await middleware.dispatch(FakeRequest(), call_next)
    middleware._requests.clear()

    assert middleware.namespace != before
    assert await middleware.dispatch(FakeRequest(), call_next) is call_next.response


async def test_forwarded_for_is_ignored_when_it_is_not_trusted(clock, redis):
    middleware = build_middleware(redis, max_requests=2, trust_forwarded_for=False)
    call_next = CallNextSpy()

    for spoofed in ("1.1.1.1", "2.2.2.2"):
        await middleware.dispatch(
            FakeRequest(host="10.0.0.1", headers={"x-forwarded-for": spoofed}), call_next
        )

    rejected = await middleware.dispatch(
        FakeRequest(host="10.0.0.1", headers={"x-forwarded-for": "3.3.3.3"}), call_next
    )

    assert rejected.status_code == 429
    assert len(call_next.calls) == 2


async def test_forwarded_for_is_honoured_when_it_is_trusted(clock, redis):
    middleware = build_middleware(redis, max_requests=1, trust_forwarded_for=True)
    call_next = CallNextSpy()

    first = FakeRequest(host="10.0.0.1", headers={"x-forwarded-for": "1.1.1.1"})
    second = FakeRequest(host="10.0.0.1", headers={"x-forwarded-for": "2.2.2.2"})

    assert await middleware.dispatch(first, call_next) is call_next.response
    assert await middleware.dispatch(second, call_next) is call_next.response

    assert (await middleware.dispatch(first, call_next)).status_code == 429


async def test_trusted_forwarded_for_uses_the_original_client_hop(clock, redis):
    middleware = build_middleware(redis, max_requests=1, trust_forwarded_for=True)
    call_next = CallNextSpy()

    await middleware.dispatch(
        FakeRequest(headers={"x-forwarded-for": " 9.9.9.9 , 10.0.0.5"}), call_next
    )

    assert [key for key in redis.store if key.endswith(":global:9.9.9.9")]


async def test_trusted_forwarded_for_falls_back_to_peer_when_header_is_absent(clock, redis):
    middleware = build_middleware(redis, max_requests=1, trust_forwarded_for=True)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(host="10.0.0.7"), call_next)

    assert [key for key in redis.store if key.endswith(":global:10.0.0.7")]


async def test_unreachable_redis_lets_the_request_through(clock, redis):
    middleware = build_middleware(redis, max_requests=1)
    call_next = CallNextSpy()
    redis.fail = True

    for _ in range(5):
        assert await middleware.dispatch(FakeRequest(), call_next) is call_next.response

    assert len(call_next.calls) == 5


async def test_unreachable_redis_is_logged_as_a_warning(clock, redis, caplog):
    middleware = build_middleware(redis, max_requests=1)
    redis.fail = True

    with caplog.at_level(logging.WARNING, logger=rate_limit_module.logger.name):
        await middleware.dispatch(FakeRequest(), CallNextSpy())

    messages = [record.getMessage() for record in caplog.records]

    assert any("redis unavailable" in message for message in messages)
    assert any("connection refused" in message for message in messages)


async def test_redis_recovering_restores_enforcement(clock, redis):
    middleware = build_middleware(redis, max_requests=1)
    call_next = CallNextSpy()
    redis.fail = True

    await middleware.dispatch(FakeRequest(), call_next)
    redis.fail = False

    assert await middleware.dispatch(FakeRequest(), call_next) is call_next.response
    assert (await middleware.dispatch(FakeRequest(), call_next)).status_code == 429


async def test_auth_defaults_are_ten_attempts_per_five_minutes():
    middleware = RateLimitMiddleware(app=None)

    assert middleware.auth_max_requests == DEFAULT_AUTH_MAX_REQUESTS == 10
    assert middleware.auth_window == DEFAULT_AUTH_WINDOW == 300


async def test_login_is_throttled_long_before_the_global_limit(clock, redis):
    middleware = build_middleware(redis, max_requests=120, auth_max_requests=3, auth_window=300)
    call_next = CallNextSpy()

    for _ in range(3):
        result = await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)
        assert result is call_next.response

    rejected = await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)

    assert rejected.status_code == 429
    assert rejected.headers["x-ratelimit-limit"] == "3"
    assert len(call_next.calls) == 3


@pytest.mark.parametrize("path", ["/api/auth/login", "/api/auth/register", "/api/auth/refresh"])
async def test_every_credential_endpoint_uses_the_strict_limit(clock, redis, path):
    middleware = build_middleware(redis, max_requests=120, auth_max_requests=2, auth_window=300)
    call_next = CallNextSpy()

    for _ in range(2):
        await middleware.dispatch(FakeRequest(path=path), call_next)

    assert (await middleware.dispatch(FakeRequest(path=path), call_next)).status_code == 429


async def test_other_endpoints_are_not_touched_by_the_strict_limit(clock, redis):
    middleware = build_middleware(redis, max_requests=10, auth_max_requests=1, auth_window=300)
    call_next = CallNextSpy()

    for _ in range(10):
        result = await middleware.dispatch(FakeRequest(path="/api/search"), call_next)
        assert result is call_next.response

    assert len(call_next.calls) == 10


async def test_exhausted_login_limit_does_not_block_other_endpoints_beyond_the_global_one(
    clock, redis
):
    middleware = build_middleware(redis, max_requests=50, auth_max_requests=1, auth_window=300)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)
    assert (
        await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)
    ).status_code == 429

    assert await middleware.dispatch(FakeRequest(path="/api/search"), call_next) is (
        call_next.response
    )


async def test_the_strict_limit_is_per_ip_so_one_attacker_cannot_lock_out_others(clock, redis):
    middleware = build_middleware(redis, max_requests=120, auth_max_requests=2, auth_window=300)
    call_next = CallNextSpy()

    for _ in range(2):
        await middleware.dispatch(FakeRequest(host="6.6.6.6", path="/api/auth/login"), call_next)

    attacker = await middleware.dispatch(
        FakeRequest(host="6.6.6.6", path="/api/auth/login"), call_next
    )
    victim = await middleware.dispatch(
        FakeRequest(host="7.7.7.7", path="/api/auth/login"), call_next
    )

    assert attacker.status_code == 429
    assert victim is call_next.response


async def test_rejected_login_attempts_do_not_extend_the_strict_window(clock, redis):
    middleware = build_middleware(redis, max_requests=120, auth_max_requests=1, auth_window=300)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)

    clock.advance(150)
    assert (
        await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)
    ).status_code == 429

    clock.advance(151)
    assert (
        await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)
        is call_next.response
    )


async def test_strict_window_reopens_after_it_elapses(clock, redis):
    middleware = build_middleware(redis, max_requests=120, auth_max_requests=1, auth_window=300)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)
    assert (
        await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)
    ).status_code == 429

    clock.advance(300)

    assert (
        await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)
        is call_next.response
    )


async def test_throttled_response_carries_the_rate_limit_headers(clock, redis):
    middleware = build_middleware(redis, max_requests=2, window=60)
    call_next = CallNextSpy()

    for _ in range(2):
        await middleware.dispatch(FakeRequest(), call_next)
    clock.advance(20)

    response = await middleware.dispatch(FakeRequest(), call_next)

    assert response.status_code == 429
    assert response.headers["x-ratelimit-limit"] == "2"
    assert response.headers["x-ratelimit-remaining"] == "0"
    assert int(response.headers["retry-after"]) == 41


async def test_auth_and_global_counters_use_separate_redis_keys(clock, redis):
    middleware = build_middleware(redis, max_requests=10, auth_max_requests=5, auth_window=300)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)

    scopes = {key.split(":")[-2] for key in redis.store}

    assert scopes == {"auth", "global"}


async def test_trailing_slash_on_login_still_hits_the_strict_limit(clock, redis):
    middleware = build_middleware(redis, max_requests=120, auth_max_requests=1, auth_window=300)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(path="/api/auth/login/"), call_next)

    assert (
        await middleware.dispatch(FakeRequest(path="/api/auth/login"), call_next)
    ).status_code == 429


def build_asgi_app(redis: FakeRedis, **kwargs) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis_factory=lambda: redis, **kwargs)

    @app.get("/api/search")
    async def search():
        return {"ok": True}

    @app.post("/api/auth/login")
    async def login():
        return {"ok": True}

    return app


async def test_asgi_login_flood_is_cut_off_by_the_strict_limit(clock, redis):
    app = build_asgi_app(redis, max_requests=120, window=60, auth_max_requests=2, auth_window=300)
    transport = httpx.ASGITransport(app=app, client=("9.9.9.9", 5000))

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        for _ in range(2):
            assert (await client.post("/api/auth/login")).status_code == 200

        response = await client.post("/api/auth/login")
        allowed = await client.get("/api/search")

    assert response.status_code == 429
    assert response.headers["x-ratelimit-limit"] == "2"
    assert response.headers["retry-after"] == "301"
    assert allowed.status_code == 200


async def test_asgi_requests_pass_when_redis_is_down(clock, redis):
    redis.fail = True
    app = build_asgi_app(redis, max_requests=1, window=60)
    transport = httpx.ASGITransport(app=app, client=("9.9.9.9", 5000))

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        for _ in range(4):
            assert (await client.get("/api/search")).status_code == 200
