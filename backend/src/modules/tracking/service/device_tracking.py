from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.subscription_guard import has_feature
from src.modules.catalog.model.catalog import Brand, Device
from src.modules.products.model.product import Cluster, Product, StoreOffer
from src.modules.products.service.comparison_service import _offer_conditions
from src.modules.stores.model.store import Store
from src.modules.tracking.model.tracking import Notification, TrackedDevice, TrackedDeviceProduct
from src.modules.tracking.service.alert_service import AlertService


class DeviceTrackingService:
    @staticmethod
    async def list_for_user(db: AsyncSession, user_id: int) -> list[dict]:
        rows = (
            await db.execute(
                select(Device.id, Device.name, Device.model_key, Brand.name.label("brand"))
                .join(TrackedDevice, TrackedDevice.device_id == Device.id)
                .join(Brand, Brand.id == Device.brand_id)
                .where(TrackedDevice.user_id == user_id)
                .order_by(Device.name)
            )
        ).all()
        return [
            {"id": r.id, "name": r.name, "model_key": r.model_key, "brand": r.brand} for r in rows
        ]

    @staticmethod
    async def available(db: AsyncSession, device_id: int):
        stmt = (
            select(Product.id, Product.canonical_name)
            .join(Cluster, Product.cluster_id == Cluster.id)
            .join(StoreOffer, StoreOffer.product_id == Product.id)
            .join(Store, Store.id == StoreOffer.store_id)
            .where(Cluster.device_id == device_id, *_offer_conditions())
            .distinct()
        )
        return (await db.execute(stmt)).all()

    @staticmethod
    async def add(db: AsyncSession, user_id: int, device_id: int):
        if await db.get(Device, device_id) is None:
            return None
        stmt = (
            insert(TrackedDevice)
            .values(user_id=user_id, device_id=device_id)
            .on_conflict_do_nothing(index_elements=["user_id", "device_id"])
            .returning(TrackedDevice.id)
        )
        new_id = (await db.execute(stmt)).scalar_one_or_none()
        if new_id is not None:
            products = await DeviceTrackingService.available(db, device_id)
            if products:
                await db.execute(
                    insert(TrackedDeviceProduct)
                    .values(
                        [
                            {"tracked_device_id": new_id, "product_id": product.id}
                            for product in products
                        ]
                    )
                    .on_conflict_do_nothing()
                )
        return {"device_id": device_id}

    @staticmethod
    async def remove(db: AsyncSession, user_id: int, device_id: int):
        await db.execute(
            delete(TrackedDevice).where(
                TrackedDevice.user_id == user_id, TrackedDevice.device_id == device_id
            )
        )

    @staticmethod
    async def scan(db: AsyncSession) -> list[Notification]:
        ids = (
            (await db.execute(select(TrackedDevice.id).order_by(TrackedDevice.id))).scalars().all()
        )
        notifications = []
        for tracked_id in ids:
            tracked = (
                await db.execute(
                    select(TrackedDevice).where(TrackedDevice.id == tracked_id).with_for_update()
                )
            ).scalar_one_or_none()
            if tracked is None or not await has_feature(db, tracked.user_id, "device_tracking"):
                continue
            device = await db.get(Device, tracked.device_id)
            for product in await DeviceTrackingService.available(db, tracked.device_id):
                added = (
                    await db.execute(
                        insert(TrackedDeviceProduct)
                        .values(tracked_device_id=tracked.id, product_id=product.id)
                        .on_conflict_do_nothing()
                        .returning(TrackedDeviceProduct.product_id)
                    )
                ).scalar_one_or_none()
                if added is None:
                    continue
                notification = Notification(
                    user_id=tracked.user_id,
                    product_id=product.id,
                    type="new_device_product",
                    channel="in_app",
                    status="pending",
                    title=f"Новая запчасть: {product.canonical_name}"[:255],
                    body=(f"Для {device.name} появилась запчасть: {product.canonical_name}")[:1000],
                    dedup_key=f"device:{tracked.id}:product:{product.id}",
                )
                db.add(notification)
                notifications.append(notification)
        await db.flush()
        await AlertService.deliver(db, notifications)
        return notifications
