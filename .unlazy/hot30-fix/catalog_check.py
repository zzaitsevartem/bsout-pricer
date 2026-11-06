import asyncio

from sqlalchemy import select

from src.database import async_session_factory, engine
from src.modules.catalog.model.catalog import Device
from src.modules.products.service.comparison_service import ComparisonService

engine.echo = False


async def main():
    async with async_session_factory() as db:
        device = (await db.execute(select(Device).where(
            Device.model_key == 'infinix-hot-30-play'
        ))).scalar_one()
        rows, total = await ComparisonService.search_catalog(db, device_id=device.id)
        assert total > 0 and rows
        print(f'HOT30_CATALOG_VERIFIED total={total} returned={len(rows)}')


asyncio.run(main())
