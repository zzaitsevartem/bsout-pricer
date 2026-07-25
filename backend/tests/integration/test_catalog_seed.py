import pytest
from sqlalchemy import func, select

from src.modules.catalog.model.catalog import (
    Brand,
    Device,
    PartType,
    PartTypeSynonym,
    QualityTier,
    QualityTierSynonym,
)
from src.modules.catalog.service.seed import seed_catalog

pytestmark = pytest.mark.integration

_MODELS = [Brand, Device, PartType, PartTypeSynonym, QualityTier, QualityTierSynonym]


async def _counts(db) -> dict[str, int]:
    result = {}
    for model in _MODELS:
        result[model.__name__] = (
            await db.execute(select(func.count()).select_from(model))
        ).scalar()
    return result


async def test_seed_is_idempotent(db_session):
    await seed_catalog(db_session)
    first = await _counts(db_session)

    await seed_catalog(db_session)
    second = await _counts(db_session)

    assert first == second
    assert first["PartType"] == 10
    assert first["QualityTier"] == 5
    assert first["Brand"] == 5
    assert first["Device"] == 4
    assert first["PartTypeSynonym"] > 0
