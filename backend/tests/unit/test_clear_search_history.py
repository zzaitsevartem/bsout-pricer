import sqlite3
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.dialects import sqlite

from src.database import get_db
from src.modules.search.controller.search import router
from src.modules.search.service.search_history_service import SearchHistoryService
from src.modules.shared import get_current_user


class HistoryDB:
    def __init__(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("CREATE TABLE search_history (id INTEGER, user_id INTEGER)")
        self.connection.executemany(
            "INSERT INTO search_history VALUES (?, ?)",
            [(i, 1) for i in range(25)] + [(99, 2)],
        )
        self.flush = AsyncMock()

    async def execute(self, statement):
        compiled = statement.compile(dialect=sqlite.dialect())
        return self.connection.execute(
            str(compiled), tuple(compiled.params[name] for name in compiled.positiontup)
        )

    def rows(self):
        return self.connection.execute("SELECT id, user_id FROM search_history").fetchall()


@pytest.mark.asyncio
async def test_clear_removes_all_25_rows_and_preserves_other_user():
    db = HistoryDB()
    try:
        await SearchHistoryService.clear_by_user(db, 1)
        assert db.rows() == [(99, 2)]
        await SearchHistoryService.clear_by_user(db, 1)
        assert db.rows() == [(99, 2)]
    finally:
        db.connection.close()


@pytest.mark.asyncio
async def test_delete_route_uses_authenticated_user_and_returns_empty_204():
    db = HistoryDB()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/search/history")
        assert response.status_code == 204
        assert response.content == b""
        assert db.rows() == [(99, 2)]
    finally:
        db.connection.close()


@pytest.mark.asyncio
async def test_anonymous_cannot_clear_history():
    app = FastAPI()
    app.include_router(router)
    db = HistoryDB()
    app.dependency_overrides[get_db] = lambda: db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/api/search/history")
        assert response.status_code in (401, 403)
        assert len(db.rows()) == 26
    finally:
        db.connection.close()
