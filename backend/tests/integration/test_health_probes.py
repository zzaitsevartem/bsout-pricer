import pytest

from src.modules.health.controller import health as health_module

pytestmark = pytest.mark.integration


async def test_liveness_never_touches_dependencies(client, monkeypatch):
    async def explode() -> None:
        raise AssertionError("проба живости не должна ходить в зависимости")

    monkeypatch.setattr(health_module, "_check_postgres", explode)
    monkeypatch.setattr(health_module, "_check_redis", explode)

    resp = await client.get("/api/health/live")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_readiness_is_ok_when_dependencies_answer(client):
    resp = await client.get("/api/health/ready")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["postgres"] == "ok"
    assert body["redis"] == "ok"


async def test_readiness_returns_503_when_postgres_is_down(client, monkeypatch):
    async def broken() -> None:
        raise ConnectionError("postgres down")

    monkeypatch.setattr(health_module, "_check_postgres", broken)

    resp = await client.get("/api/health/ready")

    assert resp.status_code == 503, resp.text
    body = resp.json()
    assert body["status"] == "degraded"
    assert body["postgres"] == "unavailable"


async def test_readiness_returns_503_when_redis_is_down(client, monkeypatch):
    async def broken() -> None:
        raise ConnectionError("redis down")

    monkeypatch.setattr(health_module, "_check_redis", broken)

    resp = await client.get("/api/health/ready")

    assert resp.status_code == 503, resp.text
    assert resp.json()["redis"] == "unavailable"


async def test_probes_do_not_leak_internal_details(client):
    body = (await client.get("/api/health/ready")).text.lower()

    for leaked in ("postgresql://", "redis://", "localhost", "5434", "password", "version"):
        assert leaked not in body, f"проба раскрывает внутреннюю деталь: {leaked}"


async def test_request_id_is_returned_and_echoed(client):
    generated = await client.get("/api/health/live")
    assert generated.headers.get("X-Request-ID")

    echoed = await client.get("/api/health/live", headers={"X-Request-ID": "trace-42"})
    assert echoed.headers.get("X-Request-ID") == "trace-42"
