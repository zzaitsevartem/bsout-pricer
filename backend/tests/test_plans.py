import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_plans_public(client: AsyncClient):
    resp = await client.get("/api/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 3


@pytest.mark.asyncio
async def test_plans_have_required_fields(client: AsyncClient):
    resp = await client.get("/api/plans")
    plans = resp.json()
    for plan in plans:
        assert "slug" in plan
        assert "name" in plan
        assert "price" in plan
        assert "period" in plan
        assert "features" in plan
        assert "tooltips" in plan
        assert isinstance(plan["features"], list)
        assert isinstance(plan["tooltips"], list)


@pytest.mark.asyncio
async def test_plans_contains_trial(client: AsyncClient):
    resp = await client.get("/api/plans")
    slugs = [p["slug"] for p in resp.json()]
    assert "trial" in slugs
    assert "basic" in slugs
    assert "advanced" in slugs
