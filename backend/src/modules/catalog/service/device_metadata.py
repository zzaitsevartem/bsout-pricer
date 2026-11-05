import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_factory
from src.modules.catalog.model.catalog import Device, DeviceAlias
from src.modules.catalog.schema.device import DeviceMetadata


def merge_metadata(device: Device, record: DeviceMetadata) -> bool:
    changed = False
    for field, value in (
        ("release_year", record.release_year),
        ("metadata_source_url", str(record.metadata_source_url)),
    ):
        if not getattr(device, field) and value:
            setattr(device, field, value)
            changed = True
    codes = list(device.model_codes or [])
    for code in record.model_codes:
        code = code.strip()
        if code and code.casefold() not in {item.casefold() for item in codes}:
            codes.append(code)
    if codes != (device.model_codes or []):
        device.model_codes = codes
        changed = True
    if not device.images and record.images:
        device.images = [image.model_dump(mode="json") for image in record.images]
        changed = True
    return changed


async def import_metadata(db: AsyncSession, records: list[DeviceMetadata]) -> dict:
    result = {"matched": 0, "updated": 0, "missing": [], "alias_conflicts": []}
    for record in records:
        device = await db.scalar(select(Device).where(Device.model_key == record.model_key))
        if device is None:
            result["missing"].append(record.model_key)
            continue
        result["matched"] += 1
        changed = merge_metadata(device, record)
        for code in device.model_codes or []:
            alias = await db.scalar(
                select(DeviceAlias).where(func.lower(DeviceAlias.alias) == code.lower())
            )
            if alias is None:
                db.add(DeviceAlias(device_id=device.id, alias=code, source="device_metadata"))
                await db.flush()
                changed = True
            elif alias.device_id != device.id:
                result["alias_conflicts"].append(code)
        result["updated"] += int(changed)
    await db.flush()
    return result


async def run(path: Path, apply: bool) -> None:
    records = [DeviceMetadata.model_validate(item) for item in json.loads(path.read_text())]
    async with async_session_factory() as db:
        result = await import_metadata(db, records)
        if apply:
            await db.commit()
        else:
            await db.rollback()
        total = await db.scalar(select(func.count(Device.id)))
        photographed = await db.scalar(
            select(func.count(Device.id)).where(func.json_array_length(Device.images) > 0)
        )
        with_year = await db.scalar(
            select(func.count(Device.id)).where(Device.release_year.is_not(None))
        )
        with_codes = await db.scalar(
            select(func.count(Device.id)).where(func.json_array_length(Device.model_codes) > 0)
        )
        print(
            json.dumps(
                {
                    **result,
                    "applied": apply,
                    "coverage": {
                        "devices": total,
                        "with_photos": photographed,
                        "with_release_year": with_year,
                        "with_model_codes": with_codes,
                    },
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args.dataset, args.apply))
