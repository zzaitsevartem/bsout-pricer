from copy import deepcopy
from decimal import Decimal
from importlib import import_module
from unittest.mock import AsyncMock

import pytest

from src.modules.parser.service.base import BaseParser, ParseResult, ParserManager
from src.modules.parser.service.parser_service import ParserService

pytestmark = pytest.mark.unit


class _StubParser(BaseParser):
    async def search(self, query):
        return []

    async def update_catalog(self, limit=None, section=None):
        return []


def test_parse_result_defaults():
    r = ParseResult(source_sku="x1", title="iPhone", price_retail=Decimal("100"))
    assert r.stock_status == "unknown"
    assert r.price_opt is None
    assert r.price_old is None
    assert r.raw == {}
    assert r.url == ""


def test_manager_registers_and_gets_by_slug():
    mgr = ParserManager()
    p = _StubParser("dns", "DNS", "https://dns.example")
    mgr.register(p)
    assert mgr.get("dns") is p
    assert mgr.get("missing") is None
    assert mgr.get_all() == [p]


def test_manager_status_shape():
    mgr = ParserManager()
    mgr.register(_StubParser("dns", "DNS", "https://dns.example"))
    status = mgr.get_statuses()[0]
    assert status["store_slug"] == "dns"
    assert status["is_running"] is False
    assert status["last_run"] is None
    assert status["errors"] == []


async def test_failed_catalog_is_not_reported_as_done(monkeypatch):
    from src.modules.cache import RedisCache

    class FailedParser(_StubParser):
        async def update_catalog(self, limit=None, section=None):
            self.errors.append("HTTP 503: sitemap unavailable")
            return []

    manager = ParserManager()
    manager.register(FailedParser("profi", "Profi", "https://example.com"))
    service = ParserService(manager)
    for method, result in (
        ("acquire_lock", True),
        ("get", None),
        ("set", None),
        ("release_lock", None),
    ):
        monkeypatch.setattr(RedisCache, method, AsyncMock(return_value=result))
    monkeypatch.setattr(service, "_resolve_store_id", AsyncMock(return_value=1))
    monkeypatch.setattr(service, "_active_offer_count", AsyncMock(return_value=0))

    result = await service.run_one(AsyncMock(), "profi", limit=200)

    assert result["status"] == "error"
    assert result["upserted"] == 0
    assert result["errors"] == ["HTTP 503: sitemap unavailable"]


async def test_nightly_catalog_queues_full_resumable_runs(monkeypatch):
    from src import worker

    enqueue = AsyncMock(return_value={"status": "queued"})
    monkeypatch.setattr(worker.settings, "parser_full_sync_enabled", True)
    monkeypatch.setattr(
        worker.parser_service, "list_parsers", lambda: [_StubParser("tgsm", "T", "")]
    )
    monkeypatch.setattr(worker.parser_service, "enqueue_run", enqueue)

    assert await worker._sync_catalog() == {"status": "queued", "stores": [{"status": "queued"}]}
    enqueue.assert_awaited_once_with("tgsm", full_sync=True)


@pytest.mark.parametrize("stop", ["failure", "continuation"])
async def test_full_catalog_commits_batches_and_resumes(monkeypatch, stop):
    from src.modules.cache import RedisCache
    from src.modules.products.service.matching_service import MatchingService

    module = import_module("src.modules.parser.service.parser_service")
    cache = {}

    async def get(key):
        return deepcopy(cache.get(key))

    async def set_value(key, value, ttl):
        cache[key] = deepcopy(value)

    async def delete(key):
        cache.pop(key, None)

    class BatchedParser(_StubParser):
        supports_catalog_batches = True
        fail = stop == "failure"

        async def catalog_urls(self, section=None):
            return ["a", "b", "c"]

        async def parse_catalog_batch(self, urls):
            if urls == ["b"] and self.fail:
                self.fail = False
                raise RuntimeError("interrupted")
            return [ParseResult(source_sku=u, title=u, price_retail=Decimal("1")) for u in urls]

    monkeypatch.setattr(RedisCache, "get", get)
    monkeypatch.setattr(RedisCache, "set", set_value)
    monkeypatch.setattr(RedisCache, "delete", delete)
    for method in ("acquire_lock", "release_lock"):
        monkeypatch.setattr(RedisCache, method, AsyncMock(return_value=True))
    monkeypatch.setattr(module, "CATALOG_BATCH_SIZE", 1)
    monkeypatch.setattr(module, "CATALOG_JOB_SECONDS", 0 if stop == "continuation" else 100000)
    enqueue = AsyncMock(return_value="next-job")
    monkeypatch.setattr(module, "enqueue_parser_run", enqueue)
    monkeypatch.setattr(
        "src.modules.catalog.service.dictionaries.load_dictionaries", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(MatchingService, "match_offer", AsyncMock())
    monkeypatch.setattr(MatchingService, "recalc_cluster_aggregates", AsyncMock())
    manager = ParserManager()
    manager.register(BatchedParser("test", "Test", ""))
    service = ParserService(manager)
    monkeypatch.setattr(service, "_resolve_store_id", AsyncMock(return_value=1))
    monkeypatch.setattr(service, "_active_offer_count", AsyncMock(return_value=0))
    monkeypatch.setattr(service, "_deactivate_stale_offers", AsyncMock(return_value=0))
    upsert = AsyncMock()
    monkeypatch.setattr(service, "upsert_offer", upsert)
    db = AsyncMock()

    if stop == "failure":
        with pytest.raises(RuntimeError, match="interrupted"):
            await service.run_one(db, "test", full_sync=True)
    else:
        first = await service.run_one(db, "test", full_sync=True)
        assert first["status"] == "continued"
        enqueue.assert_awaited_once_with("test", True, None, None)
    assert cache["parser:checkpoint:test:all"]["offset"] == 1
    assert db.commit.await_count == 1

    monkeypatch.setattr(module, "CATALOG_JOB_SECONDS", 100000)
    result = await service.run_one(db, "test", full_sync=True)

    assert result["status"] == "done"
    assert result["upserted"] == result["urls_processed"] == result["urls_total"] == 3
    assert [call.args[2].source_sku for call in upsert.await_args_list] == ["a", "b", "c"]
    assert "parser:checkpoint:test:all" not in cache
