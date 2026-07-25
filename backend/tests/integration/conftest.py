import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import src.db_metadata  # noqa: F401
from src.config import settings
from src.database import Base, get_db

pytestmark = pytest.mark.integration


def _test_database_url() -> str:
    override = os.environ.get("TEST_DATABASE_URL")
    if override:
        return override
    return settings.database_url.rsplit("/", 1)[0] + "/bscout_test"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(_test_database_url(), echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # noqa: BLE001
        await engine.dispose()
        pytest.skip(
            f"integration DB unavailable ({exc}); run `docker compose up -d` and create bscout_test"
        )
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def reset_redis_singleton():
    yield
    from src.modules.cache.service.redis_cache import close_redis

    await close_redis()


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from src.main import app
    from src.middleware.rate_limit import RateLimitMiddleware

    if app.middleware_stack is None:
        app.middleware_stack = app.build_middleware_stack()

    node = app.middleware_stack
    seen: set[int] = set()
    while node is not None and id(node) not in seen:
        seen.add(id(node))
        if isinstance(node, RateLimitMiddleware):
            node._requests.clear()
            node._since_sweep = 0
            break
        node = getattr(node, "app", None)
    yield


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    from src.main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
