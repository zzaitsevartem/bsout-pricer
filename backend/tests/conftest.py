import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base, get_db
from src.main import app
from src.modules.cache import RedisCache
from src.modules.plans.model.plan import Plan

TEST_DB_URL = "sqlite+aiosqlite://"

engine = create_async_engine(TEST_DB_URL, echo=False)

TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed plans for tests
    async with TestSessionLocal() as session:
        existing = await session.execute(select(Plan))
        if not existing.scalars().first():
            from datetime import datetime, timezone
            plans_data = [
                Plan(slug="trial", name="Пробный", price=0, period="/ 7 дней", discount="Бесплатно",
                     features=["Все 5 магазинов","Точный + частичный поиск","До 10 товаров","История цен — 3 месяца"],
                     tooltips=["Точное + частичное совпадение","До 10 отслеживаемых товаров","История цен — 3 месяца","7 дней бесплатного доступа","После окончания — автоматическое продление"],
                     featured=False, is_active=True, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
                Plan(slug="basic", name="Базовый", price=399, period="/ месяц", discount="−20% на первый платёж",
                     features=["Все 5 магазинов","Точный + частичный поиск","До 100 товаров","История цен — 3 месяца"],
                     tooltips=["Точное + частичное совпадение","До 100 отслеживаемых товаров","История цен — 3 месяца","Без уведомлений о падении цен","Без экспорта отчётов","Поддержка в рабочие часы"],
                     featured=False, is_active=True, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
                Plan(slug="advanced", name="Продвинутый", price=499, period="/ месяц", discount="−20% на первый платёж",
                     features=["Все 5 магазинов","Умный поиск (fuzzy)","До 500 товаров","Уведомления о снижении цен","Экспорт PDF/CSV","Поддержка 24/7"],
                     tooltips=["Умный поиск (fuzzy) — находит при опечатках, транслитерации, другой раскладке","До 500 отслеживаемых товаров","Уведомления о снижении цен","Экспорт отчётов PDF/CSV","Поддержка 24/7"],
                     featured=True, is_active=True, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)),
            ]
            for p in plans_data:
                session.add(p)
            await session.commit()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    mock_redis = AsyncMock(spec=RedisCache)
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()

    with patch.object(RedisCache, "exists", mock_redis.exists):
        with patch.object(RedisCache, "set", mock_redis.set):
            with patch.object(RedisCache, "delete", mock_redis.delete):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as ac:
                    yield ac

    app.dependency_overrides.clear()
