import json

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.middleware import rate_limit as rate_limit_module
from src.middleware.rate_limit import RateLimitMiddleware

pytestmark = pytest.mark.unit


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


class FakeRequest:
    def __init__(self, host: str | None = "10.0.0.1"):
        self.client = FakeClient(host) if host is not None else None


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


def build_middleware(max_requests: int = 3, window: int = 60) -> RateLimitMiddleware:
    return RateLimitMiddleware(app=None, max_requests=max_requests, window=window)


def assert_throttled(response) -> None:
    assert response.status_code == 429
    assert "Too many requests" in json.loads(response.body)["detail"]
    assert int(response.headers["retry-after"]) >= 1


async def test_requests_below_limit_pass_through(clock):
    middleware = build_middleware(max_requests=3)
    call_next = CallNextSpy()

    for _ in range(3):
        result = await middleware.dispatch(FakeRequest(), call_next)
        assert result is call_next.response

    assert len(call_next.calls) == 3


async def test_call_next_receives_the_same_request_object(clock):
    middleware = build_middleware(max_requests=3)
    call_next = CallNextSpy()
    request = FakeRequest()

    await middleware.dispatch(request, call_next)

    assert call_next.calls == [request]


async def test_request_over_the_limit_is_rejected_with_429(clock):
    middleware = build_middleware(max_requests=2)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)
    await middleware.dispatch(FakeRequest(), call_next)

    response = await middleware.dispatch(FakeRequest(), call_next)

    assert_throttled(response)
    assert len(call_next.calls) == 2


async def test_rejected_request_does_not_reach_the_endpoint(clock):
    middleware = build_middleware(max_requests=1)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)

    for _ in range(3):
        assert_throttled(await middleware.dispatch(FakeRequest(), call_next))

    assert len(call_next.calls) == 1


async def test_default_limits_allow_sixty_requests(clock):
    middleware = RateLimitMiddleware(app=None)
    call_next = CallNextSpy()

    assert middleware.max_requests == 60
    assert middleware.window == 60

    for _ in range(60):
        await middleware.dispatch(FakeRequest(), call_next)

    assert_throttled(await middleware.dispatch(FakeRequest(), call_next))


async def test_window_slides_and_counter_resets(clock):
    middleware = build_middleware(max_requests=2, window=60)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)
    await middleware.dispatch(FakeRequest(), call_next)

    assert_throttled(await middleware.dispatch(FakeRequest(), call_next))

    clock.advance(61)

    for _ in range(2):
        result = await middleware.dispatch(FakeRequest(), call_next)
        assert result is call_next.response

    assert len(call_next.calls) == 4


async def test_slot_frees_exactly_when_window_elapses(clock):
    middleware = build_middleware(max_requests=1, window=60)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)

    clock.advance(59.9)
    assert_throttled(await middleware.dispatch(FakeRequest(), call_next))

    clock.advance(0.1)
    result = await middleware.dispatch(FakeRequest(), call_next)

    assert result is call_next.response


async def test_window_slides_partially_freeing_one_slot_at_a_time(clock):
    middleware = build_middleware(max_requests=2, window=60)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)
    clock.advance(30)
    await middleware.dispatch(FakeRequest(), call_next)

    clock.advance(30)
    await middleware.dispatch(FakeRequest(), call_next)

    assert_throttled(await middleware.dispatch(FakeRequest(), call_next))

    clock.advance(30)
    await middleware.dispatch(FakeRequest(), call_next)

    assert len(call_next.calls) == 4


async def test_rejected_requests_do_not_extend_the_window(clock):
    middleware = build_middleware(max_requests=1, window=60)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)

    clock.advance(30)
    assert_throttled(await middleware.dispatch(FakeRequest(), call_next))

    clock.advance(31)
    result = await middleware.dispatch(FakeRequest(), call_next)

    assert result is call_next.response


async def test_retry_after_reflects_remaining_window(clock):
    middleware = build_middleware(max_requests=1, window=60)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(), call_next)
    clock.advance(20)

    response = await middleware.dispatch(FakeRequest(), call_next)

    assert response.status_code == 429
    assert int(response.headers["retry-after"]) == 41


async def test_separate_client_ips_have_independent_counters(clock):
    middleware = build_middleware(max_requests=2)
    call_next = CallNextSpy()

    for _ in range(2):
        await middleware.dispatch(FakeRequest("1.1.1.1"), call_next)

    assert_throttled(await middleware.dispatch(FakeRequest("1.1.1.1"), call_next))

    for _ in range(2):
        result = await middleware.dispatch(FakeRequest("2.2.2.2"), call_next)
        assert result is call_next.response

    assert_throttled(await middleware.dispatch(FakeRequest("2.2.2.2"), call_next))

    assert len(call_next.calls) == 4


async def test_exhausting_one_ip_does_not_block_another(clock):
    middleware = build_middleware(max_requests=1)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest("1.1.1.1"), call_next)

    for host in ("2.2.2.2", "3.3.3.3", "4.4.4.4"):
        result = await middleware.dispatch(FakeRequest(host), call_next)
        assert result is call_next.response


async def test_request_without_client_is_handled(clock):
    middleware = build_middleware(max_requests=2)
    call_next = CallNextSpy()

    request = FakeRequest(host=None)
    assert request.client is None

    result = await middleware.dispatch(request, call_next)

    assert result is call_next.response


async def test_clientless_requests_share_the_unknown_bucket(clock):
    middleware = build_middleware(max_requests=2)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(host=None), call_next)
    await middleware.dispatch(FakeRequest(host=None), call_next)

    assert_throttled(await middleware.dispatch(FakeRequest(host=None), call_next))


async def test_unknown_bucket_is_separate_from_real_ips(clock):
    middleware = build_middleware(max_requests=1)
    call_next = CallNextSpy()

    await middleware.dispatch(FakeRequest(host=None), call_next)

    result = await middleware.dispatch(FakeRequest("5.5.5.5"), call_next)

    assert result is call_next.response

    assert_throttled(await middleware.dispatch(FakeRequest(host=None), call_next))


async def test_middleware_instances_do_not_share_state(clock):
    first = build_middleware(max_requests=1)
    second = build_middleware(max_requests=1)
    call_next = CallNextSpy()

    await first.dispatch(FakeRequest(), call_next)

    result = await second.dispatch(FakeRequest(), call_next)

    assert result is call_next.response


async def test_idle_buckets_are_swept_and_do_not_grow_forever(clock):
    middleware = build_middleware(max_requests=5, window=60)
    call_next = CallNextSpy()

    for i in range(rate_limit_module.SWEEP_EVERY - 1):
        await middleware.dispatch(FakeRequest(f"10.0.{i // 250}.{i % 250}"), call_next)

    assert len(middleware._requests) > 1

    clock.advance(120)
    await middleware.dispatch(FakeRequest("172.16.0.1"), call_next)

    assert list(middleware._requests) == ["172.16.0.1"]


def build_asgi_app(max_requests: int) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=max_requests, window=60)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    return app


async def test_asgi_requests_under_the_limit_return_200():
    app = build_asgi_app(max_requests=3)
    transport = httpx.ASGITransport(app=app, client=("9.9.9.9", 5000))

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        for _ in range(3):
            response = await client.get("/ping")
            assert response.status_code == 200
            assert response.json() == {"ok": True}


async def test_asgi_over_the_limit_returns_429_response(clock):
    app = build_asgi_app(max_requests=1)
    transport = httpx.ASGITransport(app=app, client=("9.9.9.9", 5000))

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        assert (await client.get("/ping")).status_code == 200

        response = await client.get("/ping")

    assert response.status_code == 429
    assert response.json()["detail"].startswith("Too many requests")
    assert "retry-after" in response.headers


def test_throttled_response_keeps_cors_headers_and_preflight_is_not_throttled():
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=1, window=60)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    origin = {"Origin": "http://localhost:3000"}

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/ping", headers=origin).status_code == 200

        throttled = client.get("/ping", headers=origin)
        preflight = client.options(
            "/ping", headers={**origin, "Access-Control-Request-Method": "GET"}
        )

    assert throttled.status_code == 429
    assert throttled.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert preflight.status_code == 200


async def test_zero_limit_rejects_without_crashing(clock):
    middleware = build_middleware(max_requests=0, window=60)
    call_next = CallNextSpy()

    response = await middleware.dispatch(FakeRequest(), call_next)

    assert response.status_code == 429
    assert int(response.headers["retry-after"]) >= 1
    assert call_next.calls == []


def test_asgi_rate_limited_client_receives_429_through_the_real_stack():
    app = build_asgi_app(max_requests=1)

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/ping").status_code == 200

        response = client.get("/ping")

    assert response.status_code == 429
    assert response.json()["detail"].startswith("Too many requests")
