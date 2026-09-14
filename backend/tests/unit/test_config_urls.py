import pytest

from src.config import Settings

pytestmark = pytest.mark.unit


def test_database_url_is_async_asyncpg_dsn():
    s = Settings(
        postgres_user="u",
        postgres_password="p",
        postgres_host="db",
        postgres_port=5434,
        postgres_db="bscout",
    )
    assert s.database_url == "postgresql+asyncpg://u:p@db:5434/bscout"


def test_redis_url_points_at_db_zero():
    s = Settings(redis_host="cache", redis_port=6380)
    assert s.redis_url == "redis://cache:6380/0"
