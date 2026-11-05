from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.modules.catalog.model.catalog import Device
from src.modules.catalog.schema.device import DeviceDetail

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("/{model_key}", response_model=DeviceDetail)
async def device_detail(model_key: str, db: AsyncSession = Depends(get_db)):
    device = await db.scalar(
        select(Device)
        .where(Device.model_key == model_key)
        .options(selectinload(Device.brand), selectinload(Device.aliases))
    )
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceDetail(
        id=device.id,
        model_key=device.model_key,
        name=device.name,
        brand=device.brand,
        aliases=sorted(alias.alias for alias in device.aliases),
        model_codes=device.model_codes,
        release_year=device.release_year,
        images=device.images,
        metadata_source_url=device.metadata_source_url,
    )
