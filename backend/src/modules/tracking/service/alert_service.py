from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.middleware.subscription_guard import has_feature
from src.modules.products.model.product import Product
from src.modules.products.service.comparison_service import _money, _offer_aggregate_subquery
from src.modules.tracking.model.tracking import Notification, TrackedProduct
from src.modules.tracking.service.notifier import (
    DEFAULT_CHANNEL,
    NotifierError,
    get_notifier,
)

PRICE_DROP = "price_drop"
TARGET_REACHED = "target_reached"
ALERTS_FEATURE = "price_alerts"

STATUS_PENDING = "pending"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"

TITLE_MAX = 255
BODY_MAX = 1000
ERROR_MAX = 500


@dataclass
class AlertEvent:
    tracked: TrackedProduct
    type: str
    old_price: Decimal | None
    new_price: Decimal


def _amount(value: Decimal) -> str:
    return f"{value.normalize():f}" if value == value.to_integral_value() else f"{value:f}"


def _dedup_key(event: AlertEvent) -> str:
    return f"tp{event.tracked.id}:{event.type}:{event.new_price:f}"


def _title(event: AlertEvent, product_name: str) -> str:
    if event.type == TARGET_REACHED:
        prefix = "Цена достигла цели"
    else:
        prefix = "Цена снизилась"
    return f"{prefix}: {product_name}"[:TITLE_MAX]


def _body(event: AlertEvent, product_name: str) -> str:
    new_price = _amount(event.new_price)
    if event.type == TARGET_REACHED and event.tracked.target_price is not None:
        target = _amount(_money(event.tracked.target_price))
        text = (
            f"«{product_name}»: минимальная цена {new_price} ₽ — "
            f"это не выше вашей цели {target} ₽."
        )
    elif event.old_price is not None:
        old_price = _amount(event.old_price)
        diff = _amount(_money(event.old_price - event.new_price))
        text = (
            f"«{product_name}»: минимальная цена снизилась с {old_price} ₽ "
            f"до {new_price} ₽ (−{diff} ₽)."
        )
    else:
        text = f"«{product_name}»: минимальная цена {new_price} ₽."
    return text[:BODY_MAX]


class AlertService:
    @staticmethod
    async def scan_for_drops(
        db: AsyncSession,
        product_ids: Iterable[int] | None = None,
        channel: str = DEFAULT_CHANNEL,
    ) -> list[Notification]:
        tracked = await AlertService._load_tracked(db, product_ids)
        if not tracked:
            return []

        prices = await AlertService._min_prices(db, {item.product_id for item in tracked})

        events: list[AlertEvent] = []
        for item in tracked:
            new_price = prices.get(item.product_id)
            if new_price is None:
                continue
            event_type = AlertService._classify(item, new_price)
            old_price = _money(item.last_seen_price)
            item.last_seen_price = new_price
            if event_type is not None:
                events.append(AlertEvent(item, event_type, old_price, new_price))
        await db.flush()

        if not events:
            return []

        allowed = await AlertService._users_with_alerts(db, {e.tracked.user_id for e in events})
        events = [event for event in events if event.tracked.user_id in allowed]
        if not events:
            return []

        names = await AlertService._product_names(db, {e.tracked.product_id for e in events})

        created: list[Notification] = []
        notified: list[TrackedProduct] = []
        for event in events:
            notification = await AlertService._insert(db, event, names, channel)
            if notification is not None:
                created.append(notification)
                notified.append(event.tracked)

        now = datetime.now(timezone.utc)
        for item in notified:
            item.last_notified_at = now
        await db.flush()

        await AlertService.deliver(db, created)
        return created

    @staticmethod
    async def deliver(db: AsyncSession, notifications: list[Notification]) -> list[Notification]:
        if not notifications:
            return []
        for notification in notifications:
            try:
                notifier = get_notifier(notification.channel)
                await notifier.send(notification)
            except NotifierError as exc:
                notification.status = STATUS_FAILED
                notification.error = str(exc)[:ERROR_MAX]
        await db.flush()
        return notifications

    @staticmethod
    async def list_notifications(
        db: AsyncSession,
        user_id: int,
        unread: bool | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Notification], int]:
        conditions = [Notification.user_id == user_id]
        if unread is True:
            conditions.append(Notification.read_at.is_(None))
        elif unread is False:
            conditions.append(Notification.read_at.is_not(None))

        total = (
            await db.execute(select(func.count(Notification.id)).where(*conditions))
        ).scalar() or 0

        stmt = (
            select(Notification)
            .where(*conditions)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        rows = list((await db.execute(stmt)).scalars().all())
        return rows, total

    @staticmethod
    async def unread_count(db: AsyncSession, user_id: int) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id, Notification.read_at.is_(None)
        )
        return (await db.execute(stmt)).scalar() or 0

    @staticmethod
    async def get_own(db: AsyncSession, user_id: int, notification_id: int) -> Notification | None:
        stmt = select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def mark_read(
        db: AsyncSession, user_id: int, notification_id: int
    ) -> Notification | None:
        notification = await AlertService.get_own(db, user_id, notification_id)
        if notification is None:
            return None
        if notification.read_at is None:
            notification.read_at = datetime.now(timezone.utc)
            await db.flush()
        return notification

    @staticmethod
    def _classify(item: TrackedProduct, new_price: Decimal) -> str | None:
        if item.target_price is not None and new_price <= _money(item.target_price):
            return TARGET_REACHED
        old_price = _money(item.last_seen_price)
        if item.notify_on_any_drop and old_price is not None and new_price < old_price:
            return PRICE_DROP
        return None

    @staticmethod
    async def _load_tracked(
        db: AsyncSession, product_ids: Iterable[int] | None
    ) -> list[TrackedProduct]:
        stmt = select(TrackedProduct).where(TrackedProduct.is_active.is_(True))
        if product_ids is not None:
            ids = list(product_ids)
            if not ids:
                return []
            stmt = stmt.where(TrackedProduct.product_id.in_(ids))
        stmt = stmt.order_by(TrackedProduct.id)
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def _min_prices(db: AsyncSession, product_ids: set[int]) -> dict[int, Decimal]:
        if not product_ids:
            return {}
        agg = _offer_aggregate_subquery()
        stmt = select(agg.c.product_id, agg.c.min_price_retail).where(
            agg.c.product_id.in_(product_ids)
        )
        rows = (await db.execute(stmt)).all()
        return {
            row.product_id: _money(row.min_price_retail)
            for row in rows
            if row.min_price_retail is not None
        }

    @staticmethod
    async def _users_with_alerts(db: AsyncSession, user_ids: set[int]) -> set[int]:
        allowed: set[int] = set()
        for user_id in user_ids:
            if await has_feature(db, user_id, ALERTS_FEATURE):
                allowed.add(user_id)
        return allowed

    @staticmethod
    async def _product_names(db: AsyncSession, product_ids: set[int]) -> dict[int, str]:
        if not product_ids:
            return {}
        stmt = select(Product.id, Product.canonical_name).where(Product.id.in_(product_ids))
        return {row.id: row.canonical_name for row in (await db.execute(stmt)).all()}

    @staticmethod
    async def _insert(
        db: AsyncSession, event: AlertEvent, names: dict[int, str], channel: str
    ) -> Notification | None:
        product_name = names.get(event.tracked.product_id) or f"товар #{event.tracked.product_id}"
        notification = Notification(
            user_id=event.tracked.user_id,
            tracked_product_id=event.tracked.id,
            product_id=event.tracked.product_id,
            type=event.type,
            channel=channel,
            status=STATUS_PENDING,
            title=_title(event, product_name),
            body=_body(event, product_name),
            old_price=event.old_price,
            new_price=event.new_price,
            dedup_key=_dedup_key(event),
        )
        try:
            async with db.begin_nested():
                db.add(notification)
                await db.flush()
        except IntegrityError:
            return None
        return notification
