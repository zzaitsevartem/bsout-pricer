from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.model.catalog import (
    Brand,
    Device,
    PartType,
    PartTypeSynonym,
    QualityTier,
    QualityTierSynonym,
)

PART_TYPES: dict[str, tuple[str, list[str]]] = {
    "display": ("Дисплей", ["дисплей", "экран", "display", "lcd", "модуль"]),
    "battery": ("Аккумулятор", ["аккумулятор", "батарея", "акб", "battery"]),
    "back_cover": ("Задняя крышка", ["задняя крышка", "крышка", "back cover"]),
    "charging_port": (
        "Разъём зарядки",
        ["разъём зарядки", "разъем зарядки", "шлейф зарядки", "charging port"],
    ),
    "camera": ("Камера", ["камера", "camera"]),
    "glass": ("Стекло", ["стекло", "защитное стекло", "glass"]),
    "frame": ("Рамка", ["рамка", "корпус", "frame"]),
    "speaker": ("Динамик", ["динамик", "speaker", "спикер"]),
    "microphone": ("Микрофон", ["микрофон", "microphone"]),
    "board": ("Плата", ["плата", "материнская плата", "board", "motherboard"]),
}

QUALITY_TIERS: dict[str, tuple[str, int, list[str]]] = {
    "original": ("Оригинал", 0, ["оригинал", "orig", "original", "оем оригинал"]),
    "oem_hq": ("OEM (высокое качество)", 1, ["oem", "oem hq", "hq", "premium"]),
    "copy": ("Копия / аналог", 2, ["копия", "copy", "аналог", "china"]),
    "service": ("Сервисный", 3, ["service", "service pack", "сервисный", "восстановленный"]),
    "unknown": ("Не определено", 9, []),
}

BRANDS: dict[str, str] = {
    "Apple": "apple",
    "Samsung": "samsung",
    "Xiaomi": "xiaomi",
    "Huawei": "huawei",
    "Honor": "honor",
}

DEVICES: list[tuple[str, str, str]] = [
    ("Apple", "iPhone 13", "apple-iphone-13"),
    ("Apple", "iPhone 14", "apple-iphone-14"),
    ("Samsung", "Galaxy S23", "samsung-galaxy-s23"),
    ("Xiaomi", "Redmi Note 12", "xiaomi-redmi-note-12"),
]


async def _get_or_create_part_type(db: AsyncSession, code: str, name_ru: str) -> PartType:
    existing = (
        await db.execute(select(PartType).where(PartType.code == code))
    ).scalar_one_or_none()
    if existing:
        return existing
    part_type = PartType(code=code, name_ru=name_ru)
    db.add(part_type)
    await db.flush()
    return part_type


async def _get_or_create_quality_tier(
    db: AsyncSession, code: str, name_ru: str, rank: int
) -> QualityTier:
    existing = (
        await db.execute(select(QualityTier).where(QualityTier.code == code))
    ).scalar_one_or_none()
    if existing:
        return existing
    tier = QualityTier(code=code, name_ru=name_ru, rank=rank)
    db.add(tier)
    await db.flush()
    return tier


async def _get_or_create_brand(db: AsyncSession, name: str, slug: str) -> Brand:
    existing = (await db.execute(select(Brand).where(Brand.name == name))).scalar_one_or_none()
    if existing:
        return existing
    brand = Brand(name=name, slug=slug)
    db.add(brand)
    await db.flush()
    return brand


async def _ensure_synonym(
    db: AsyncSession, model, fk_field: str, parent_id: int, synonym: str
) -> None:
    existing = (
        await db.execute(select(model).where(model.synonym == synonym))
    ).scalar_one_or_none()
    if existing:
        return
    db.add(model(**{fk_field: parent_id, "synonym": synonym}))
    await db.flush()


async def seed_catalog(db: AsyncSession) -> None:
    for code, (name_ru, synonyms) in PART_TYPES.items():
        part_type = await _get_or_create_part_type(db, code, name_ru)
        for synonym in synonyms:
            await _ensure_synonym(db, PartTypeSynonym, "part_type_id", part_type.id, synonym)

    for code, (name_ru, rank, synonyms) in QUALITY_TIERS.items():
        tier = await _get_or_create_quality_tier(db, code, name_ru, rank)
        for synonym in synonyms:
            await _ensure_synonym(db, QualityTierSynonym, "quality_tier_id", tier.id, synonym)

    brands: dict[str, Brand] = {}
    for name, slug in BRANDS.items():
        brands[name] = await _get_or_create_brand(db, name, slug)

    for brand_name, device_name, model_key in DEVICES:
        brand = brands.get(brand_name)
        if brand is None:
            continue
        existing = (
            await db.execute(select(Device).where(Device.model_key == model_key))
        ).scalar_one_or_none()
        if existing is None:
            db.add(Device(brand_id=brand.id, name=device_name, model_key=model_key))
            await db.flush()
