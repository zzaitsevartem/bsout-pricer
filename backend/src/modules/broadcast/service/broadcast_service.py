import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.modules.auth.model.user import Subscription, User
from src.modules.broadcast.model.broadcast import (
    Broadcast,
    BroadcastAudience,
    BroadcastRecipient,
    BroadcastStatus,
    RecipientStatus,
)
from src.modules.broadcast.schema.broadcast import (
    BroadcastCreateRequest,
    BroadcastPreviewRequest,
)
from src.modules.mail import get_mailer

BROADCAST_QUEUE_JOB = "send_broadcast"

DEFAULT_PER_PAGE = 10
MAX_PER_PAGE = 50
SAMPLE_LIMIT = 5
ERROR_MAX_LEN = 500

logger = logging.getLogger(__name__)


class BroadcastError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_emails(emails: list[str] | None) -> list[str]:
    if not emails:
        return []
    seen: dict[str, str] = {}
    for raw in emails:
        normalized = raw.strip().lower()
        if not normalized:
            continue
        seen.setdefault(normalized, normalized)
    return list(seen.values())


def _audience_query(audience: BroadcastAudience):
    if audience == BroadcastAudience.all_active:
        return select(User).where(User.is_active.is_(True))
    if audience == BroadcastAudience.verified:
        return select(User).where(User.email_verified_at.isnot(None), User.is_active.is_(True))
    if audience == BroadcastAudience.subscribers:
        return (
            select(User)
            .join(Subscription, Subscription.user_id == User.id)
            .where(
                Subscription.is_active.is_(True),
                Subscription.end_date > _now(),
                User.is_active.is_(True),
            )
            .distinct()
        )
    raise BroadcastError("Некорректная аудитория рассылки", 422)


async def _emails_for_request(
    db: AsyncSession, request: BroadcastCreateRequest | BroadcastPreviewRequest
) -> tuple[int, list[str]]:
    if request.audience == BroadcastAudience.custom:
        emails = normalize_emails(request.recipient_emails)
        if not emails:
            raise BroadcastError("Укажите хотя бы один адрес получателя", 422)
        maximum = settings.broadcast_max_custom_recipients
        if len(emails) > maximum:
            raise BroadcastError(f"Для ручной рассылки допустимо не более {maximum} адресов", 422)
        return len(emails), emails[:SAMPLE_LIMIT]

    if request.recipient_emails:
        raise BroadcastError("Поле recipient_emails допустимо только для аудитории custom", 422)

    stmt = _audience_query(request.audience)
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    if not total:
        return 0, []
    users = list((await db.execute(stmt.limit(SAMPLE_LIMIT))).scalars().all())
    return total, [user.email for user in users]


class BroadcastService:
    @staticmethod
    async def preview(db: AsyncSession, request: BroadcastPreviewRequest) -> dict:
        total, sample = await _emails_for_request(db, request)
        return {"recipient_count": total, "sample_emails": sample}

    @staticmethod
    async def create(
        db: AsyncSession, request: BroadcastCreateRequest, creator_id: int
    ) -> Broadcast:
        recipient_emails = None
        if request.audience == BroadcastAudience.custom:
            recipient_emails = normalize_emails(request.recipient_emails)
            if not recipient_emails:
                raise BroadcastError("Укажите хотя бы один адрес получателя", 422)
            maximum = settings.broadcast_max_custom_recipients
            if len(recipient_emails) > maximum:
                raise BroadcastError(
                    f"Для ручной рассылки допустимо не более {maximum} адресов", 422
                )
        elif request.recipient_emails:
            raise BroadcastError("Поле recipient_emails допустимо только для аудитории custom", 422)

        total, _ = await _emails_for_request(db, request)
        broadcast = Broadcast(
            name=request.name,
            audience=request.audience,
            subject=request.subject,
            text=request.text,
            html=request.html,
            status=BroadcastStatus.draft,
            total_recipients=total,
            recipient_emails=recipient_emails,
            created_by=creator_id,
        )
        db.add(broadcast)
        await db.flush()
        return broadcast

    @staticmethod
    async def send_test(broadcast: Broadcast, to: str) -> str:
        mailer = get_mailer()
        await mailer.send(
            to=to, subject=broadcast.subject, text=broadcast.text, html=broadcast.html
        )
        return to

    @staticmethod
    async def _enqueue_broadcast(broadcast_id: int) -> bool:
        from arq import create_pool
        from arq.connections import RedisSettings

        pool = await create_pool(
            RedisSettings(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
            )
        )
        try:
            await pool.enqueue_job(BROADCAST_QUEUE_JOB, broadcast_id)
        finally:
            await pool.close()
        return True

    @staticmethod
    async def launch(db: AsyncSession, broadcast: Broadcast) -> Broadcast:
        if broadcast.status is not BroadcastStatus.draft:
            raise BroadcastError("Запустить можно только черновик рассылки", 409)

        if broadcast.audience == BroadcastAudience.custom:
            emails = normalize_emails(broadcast.recipient_emails)
            if not emails:
                raise BroadcastError("В рассылке нет адресов получателей", 422)
            recipients = [
                BroadcastRecipient(broadcast_id=broadcast.id, email=email) for email in emails
            ]
            total = len(emails)
        else:
            stmt = _audience_query(broadcast.audience)
            users = list((await db.execute(stmt)).scalars().all())
            recipients = [
                BroadcastRecipient(broadcast_id=broadcast.id, user_id=user.id, email=user.email)
                for user in users
            ]
            total = len(users)

        db.add_all(recipients)
        broadcast.total_recipients = total
        broadcast.sent_count = 0
        broadcast.failed_count = 0
        broadcast.error_summary = None
        broadcast.status = BroadcastStatus.queued
        await db.commit()

        enqueued = False
        try:
            enqueued = await BroadcastService._enqueue_broadcast(broadcast.id)
        except Exception:
            logger.exception("broadcast %s enqueue failed", broadcast.id)

        if not enqueued:
            await db.execute(
                delete(BroadcastRecipient).where(BroadcastRecipient.broadcast_id == broadcast.id)
            )
            broadcast.status = BroadcastStatus.draft
            broadcast.total_recipients = 0
            await db.commit()
            raise BroadcastError(
                "Очередь задач недоступна — рассылка не запущена. "
                "Убедитесь, что Redis и воркер (arq src.worker.WorkerSettings) работают.",
                503,
            )

        return broadcast

    @staticmethod
    async def cancel(db: AsyncSession, broadcast: Broadcast) -> Broadcast:
        if broadcast.status not in (BroadcastStatus.queued, BroadcastStatus.running):
            raise BroadcastError("Отменить можно только активную рассылку", 409)
        broadcast.status = BroadcastStatus.cancelled
        broadcast.finished_at = _now()
        await db.commit()
        return broadcast

    @staticmethod
    async def delete(db: AsyncSession, broadcast: Broadcast) -> None:
        if broadcast.status in (BroadcastStatus.queued, BroadcastStatus.running):
            raise BroadcastError("Нельзя удалить активную рассылку", 409)
        await db.execute(delete(Broadcast).where(Broadcast.id == broadcast.id))

    @staticmethod
    async def paginate(
        db: AsyncSession, page: int = 1, per_page: int = DEFAULT_PER_PAGE
    ) -> tuple[list[Broadcast], int]:
        total = (await db.execute(select(func.count(Broadcast.id)))).scalar() or 0
        rows = list(
            (
                await db.execute(
                    select(Broadcast)
                    .order_by(Broadcast.created_at.desc(), Broadcast.id.desc())
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                )
            )
            .scalars()
            .all()
        )
        return rows, total

    @staticmethod
    async def get(db: AsyncSession, broadcast_id: int) -> Broadcast | None:
        return await db.get(Broadcast, broadcast_id)

    @staticmethod
    async def list_recipients(
        db: AsyncSession,
        broadcast_id: int,
        status_filter: RecipientStatus | None = None,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE,
    ) -> tuple[list[BroadcastRecipient], int]:
        stmt = select(BroadcastRecipient).where(BroadcastRecipient.broadcast_id == broadcast_id)
        if status_filter is not None:
            stmt = stmt.where(BroadcastRecipient.status == status_filter)
        total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
        rows = list(
            (
                await db.execute(
                    stmt.order_by(
                        BroadcastRecipient.created_at.desc(), BroadcastRecipient.id.desc()
                    )
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                )
            )
            .scalars()
            .all()
        )
        return rows, total

    @staticmethod
    async def run_broadcast_job(broadcast_id: int, db: AsyncSession | None = None) -> dict:
        if db is not None:
            return await BroadcastService._run_broadcast_with_session(broadcast_id, db)

        from src.database import async_session_factory

        async with async_session_factory() as session:
            return await BroadcastService._run_broadcast_with_session(broadcast_id, session)

    @staticmethod
    async def _run_broadcast_with_session(broadcast_id: int, db: AsyncSession) -> dict:
        batch_size = settings.broadcast_batch_size
        delay = settings.broadcast_send_delay_seconds

        broadcast = await db.get(Broadcast, broadcast_id)
        if broadcast is None:
            return {"status": "not_found", "broadcast_id": broadcast_id}

        if broadcast.status is BroadcastStatus.queued:
            broadcast.status = BroadcastStatus.running
            broadcast.started_at = _now()
            await db.commit()
        if broadcast.status is not BroadcastStatus.running:
            return {
                "status": "skipped",
                "broadcast_id": broadcast_id,
                "reason": broadcast.status.value,
            }

        await db.execute(
            update(BroadcastRecipient)
            .where(
                BroadcastRecipient.broadcast_id == broadcast_id,
                BroadcastRecipient.status == RecipientStatus.sending,
            )
            .values(status=RecipientStatus.pending)
            .execution_options(synchronize_session=False)
        )
        await db.commit()

        mailer = get_mailer()

        while True:
            await db.refresh(broadcast)
            if broadcast.status is not BroadcastStatus.running:
                break

            ids = list(
                (
                    await db.execute(
                        select(BroadcastRecipient.id)
                        .where(
                            BroadcastRecipient.broadcast_id == broadcast_id,
                            BroadcastRecipient.status == RecipientStatus.pending,
                        )
                        .order_by(BroadcastRecipient.id)
                        .limit(batch_size)
                    )
                )
                .scalars()
                .all()
            )
            if not ids:
                break

            claimed = list(
                (
                    await db.execute(
                        update(BroadcastRecipient)
                        .where(BroadcastRecipient.id.in_(ids))
                        .values(status=RecipientStatus.sending, error=None)
                        .returning(BroadcastRecipient.id, BroadcastRecipient.email)
                        .execution_options(synchronize_session=False)
                    )
                ).all()
            )
            if not claimed:
                continue

            sent_ids: list[int] = []
            failed: list[tuple[int, str]] = []
            for recipient_id, email in claimed:
                try:
                    await mailer.send(
                        to=email,
                        subject=broadcast.subject,
                        text=broadcast.text,
                        html=broadcast.html,
                    )
                    sent_ids.append(recipient_id)
                except Exception as exc:  # noqa: BLE001
                    message = str(exc) or "SMTP failure"
                    failed.append((recipient_id, message[:ERROR_MAX_LEN]))
                if delay > 0:
                    await asyncio.sleep(delay)

            if sent_ids:
                await db.execute(
                    update(BroadcastRecipient)
                    .where(BroadcastRecipient.id.in_(sent_ids))
                    .values(status=RecipientStatus.sent, sent_at=_now(), error=None)
                    .execution_options(synchronize_session=False)
                )
            for recipient_id, error in failed:
                await db.execute(
                    update(BroadcastRecipient)
                    .where(BroadcastRecipient.id == recipient_id)
                    .values(status=RecipientStatus.failed, error=error)
                    .execution_options(synchronize_session=False)
                )

            broadcast.sent_count += len(sent_ids)
            broadcast.failed_count += len(failed)
            await db.commit()

        await db.refresh(broadcast)
        remaining = (
            await db.execute(
                select(func.count(BroadcastRecipient.id)).where(
                    BroadcastRecipient.broadcast_id == broadcast_id,
                    BroadcastRecipient.status.in_(
                        (RecipientStatus.pending, RecipientStatus.sending)
                    ),
                )
            )
        ).scalar() or 0

        if broadcast.status is BroadcastStatus.running and remaining == 0:
            broadcast.status = BroadcastStatus.completed
            broadcast.finished_at = _now()
            await db.commit()
            return {"status": "completed", "broadcast_id": broadcast_id}

        return {
            "status": broadcast.status.value,
            "broadcast_id": broadcast_id,
            "remaining_recipients": remaining,
        }
