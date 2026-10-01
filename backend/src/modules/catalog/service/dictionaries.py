from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.model.catalog import (
    Color,
    ColorSynonym,
    Device,
    DeviceAlias,
    PartType,
    PartTypeSynonym,
    QualityTier,
    QualityTierSynonym,
    Stopword,
)
from src.modules.catalog.service.normalizer import normalize


@dataclass(frozen=True)
class Dictionaries:
    device_by_alias: dict[str, int]
    device_model_key: dict[int, str]
    device_brand: dict[int, int]
    part_type_by_synonym: dict[str, int]
    part_type_code: dict[int, str]
    quality_by_synonym: dict[str, int]
    quality_code: dict[int, str]
    color_by_synonym: dict[str, int]
    color_code: dict[int, str]
    stopwords: frozenset[str]


def _add_key(target: dict[str, int], raw: str, value: int) -> None:
    key = normalize(raw)
    if key:
        target.setdefault(key, value)


async def load_dictionaries(db: AsyncSession) -> Dictionaries:
    devices = (await db.execute(select(Device))).scalars().all()
    device_aliases = (await db.execute(select(DeviceAlias))).scalars().all()
    part_types = (await db.execute(select(PartType))).scalars().all()
    part_type_synonyms = (await db.execute(select(PartTypeSynonym))).scalars().all()
    quality_tiers = (await db.execute(select(QualityTier))).scalars().all()
    quality_synonyms = (await db.execute(select(QualityTierSynonym))).scalars().all()
    colors = (await db.execute(select(Color))).scalars().all()
    color_synonyms = (await db.execute(select(ColorSynonym))).scalars().all()
    stopwords = (await db.execute(select(Stopword))).scalars().all()

    device_by_alias: dict[str, int] = {}
    device_model_key: dict[int, str] = {}
    device_brand: dict[int, int] = {}
    for device in devices:
        device_model_key[device.id] = device.model_key
        device_brand[device.id] = device.brand_id
        _add_key(device_by_alias, device.model_key.replace("-", " "), device.id)
        _add_key(device_by_alias, device.name, device.id)
    for alias in device_aliases:
        _add_key(device_by_alias, alias.alias, alias.device_id)

    part_type_by_synonym: dict[str, int] = {}
    part_type_code: dict[int, str] = {}
    for part_type in part_types:
        part_type_code[part_type.id] = part_type.code
        _add_key(part_type_by_synonym, part_type.name_ru, part_type.id)
    for synonym in part_type_synonyms:
        _add_key(part_type_by_synonym, synonym.synonym, synonym.part_type_id)

    quality_by_synonym: dict[str, int] = {}
    quality_code: dict[int, str] = {}
    for tier in quality_tiers:
        quality_code[tier.id] = tier.code
    for synonym in quality_synonyms:
        _add_key(quality_by_synonym, synonym.synonym, synonym.quality_tier_id)

    color_by_synonym: dict[str, int] = {}
    color_code: dict[int, str] = {}
    for color in colors:
        color_code[color.id] = color.code
        _add_key(color_by_synonym, color.name_ru, color.id)
    for synonym in color_synonyms:
        _add_key(color_by_synonym, synonym.synonym, synonym.color_id)

    normalized_stopwords = {normalize(word.word) for word in stopwords}

    return Dictionaries(
        device_by_alias=device_by_alias,
        device_model_key=device_model_key,
        device_brand=device_brand,
        part_type_by_synonym=part_type_by_synonym,
        part_type_code=part_type_code,
        quality_by_synonym=quality_by_synonym,
        quality_code=quality_code,
        color_by_synonym=color_by_synonym,
        color_code=color_code,
        stopwords=frozenset(word for word in normalized_stopwords if word),
    )
