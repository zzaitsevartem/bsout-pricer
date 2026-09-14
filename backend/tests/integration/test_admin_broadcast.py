from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from src.config import settings
from src.modules.auth.model.user import User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.broadcast.model.broadcast import (
    Broadcast,
    BroadcastRecipient,
    BroadcastStatus,
    RecipientStatus,
)
from src.modules.broadcast.service.broadcast_service import BroadcastService

pytestmark = pytest.mark.integration

BROADCAST_URL = "/api/admin/broadcasts"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(
    db, email: str, *, is_admin: bool = False, is_active: bool = True, verified: bool = True
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Broadcast User",
        is_active=is_active,
        is_admin=is_admin,
        email_verified_at=datetime.now(timezone.utc) if verified else None,
    )
    db.add(user)
    await db.flush()
    return user


async def _admin_headers(db, email: str = "badmin@example.com") -> dict[str, str]:
    admin = await _make_user(db, email, is_admin=True, verified=False)
    return _auth(create_access_token(admin.id))


def _payload(
    *,
    audience: str = "custom",
    emails: list[str] | None = None,
    name: str = "Тест рассылки",
) -> dict:
    payload = {
        "name": name,
        "audience": audience,
        "subject": "Тестовая тема",
        "text": "Тело письма",
        "html": "<p>Тело письма</p>",
    }
    if emails is not None:
        payload["recipient_emails"] = emails
    return payload


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, to: str, subject: str, text: str, html: str | None = None) -> None:
        self.sent.append((to, subject, text))


async def _broadcast_by_id(db, broadcast_id: int) -> Broadcast | None:
    return await db.get(Broadcast, broadcast_id)


async def test_create_custom_draft_counts_recipients(db_session, client):
    headers = await _admin_headers(db_session)

    resp = await client.post(
        BROADCAST_URL,
        headers=headers,
        json=_payload(emails=["a@example.com", "B@example.com", "a@example.com"]),
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "draft"
    assert data["total_recipients"] == 2
    assert data["audience"] == "custom"


async def test_create_counts_only_matching_verified_users(db_session, client):
    headers = await _admin_headers(db_session)
    await _make_user(db_session, "ok@example.com", verified=True, is_active=True)
    await _make_user(db_session, "inactive@example.com", verified=True, is_active=False)
    await _make_user(db_session, "unverified@example.com", verified=False, is_active=True)

    resp = await client.post(BROADCAST_URL, headers=headers, json=_payload(audience="verified"))

    assert resp.status_code == 201
    assert resp.json()["total_recipients"] == 1


async def test_preview_returns_count_and_sample(db_session, client):
    headers = await _admin_headers(db_session)
    await _make_user(db_session, "one@example.com", verified=True)
    await _make_user(db_session, "two@example.com", verified=True)

    resp = await client.post(
        f"{BROADCAST_URL}/preview",
        headers=headers,
        json=_payload(audience="verified"),
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["recipient_count"] == 2
    assert len(data["sample_emails"]) == 2

    custom = await client.post(
        f"{BROADCAST_URL}/preview",
        headers=headers,
        json=_payload(emails=["x@example.com", "y@example.com"]),
    )
    assert custom.json()["recipient_count"] == 2


async def test_create_rejects_empty_custom_list(db_session, client):
    headers = await _admin_headers(db_session)

    resp = await client.post(BROADCAST_URL, headers=headers, json=_payload(emails=[]))

    assert resp.status_code == 422


async def test_create_rejects_emails_for_non_custom_audience(db_session, client):
    headers = await _admin_headers(db_session)

    resp = await client.post(
        BROADCAST_URL,
        headers=headers,
        json=_payload(audience="all_active", emails=["x@example.com"]),
    )

    assert resp.status_code == 422


async def test_launch_custom_creates_snapshot_and_queues(db_session, client, monkeypatch):
    headers = await _admin_headers(db_session)

    async def ok_enqueue(_: int) -> bool:
        return True

    monkeypatch.setattr(BroadcastService, "_enqueue_broadcast", staticmethod(ok_enqueue))

    created = await client.post(
        BROADCAST_URL, headers=headers, json=_payload(emails=["a@example.com", "b@example.com"])
    )
    broadcast_id = created.json()["id"]

    resp = await client.post(f"{BROADCAST_URL}/{broadcast_id}/launch", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert data["total_recipients"] == 2

    rows = (
        (
            await db_session.execute(
                select(BroadcastRecipient).where(BroadcastRecipient.broadcast_id == broadcast_id)
            )
        )
        .scalars()
        .all()
    )
    assert {row.email for row in rows} == {"a@example.com", "b@example.com"}
    assert all(row.status == RecipientStatus.pending for row in rows)


async def test_launch_custom_sends_only_to_typed_emails(db_session, client, monkeypatch):
    headers = await _admin_headers(db_session)
    await _make_user(db_session, "v1@example.com", verified=True)

    async def ok_enqueue(_: int) -> bool:
        return True

    monkeypatch.setattr(BroadcastService, "_enqueue_broadcast", staticmethod(ok_enqueue))

    created = await client.post(
        BROADCAST_URL,
        headers=headers,
        json=_payload(audience="custom", emails=["org@partner.com"]),
    )
    broadcast_id = created.json()["id"]
    resp = await client.post(f"{BROADCAST_URL}/{broadcast_id}/launch", headers=headers)

    assert resp.status_code == 200
    rows = (
        (
            await db_session.execute(
                select(BroadcastRecipient).where(BroadcastRecipient.broadcast_id == broadcast_id)
            )
        )
        .scalars()
        .all()
    )
    assert {row.email for row in rows} == {"org@partner.com"}
    assert all(row.user_id is None for row in rows)


async def test_launch_verified_snapshots_users_with_user_id(db_session, client, monkeypatch):
    headers = await _admin_headers(db_session)
    await _make_user(db_session, "u1@example.com", verified=True)
    await _make_user(db_session, "u2@example.com", verified=True)

    async def ok_enqueue(_: int) -> bool:
        return True

    monkeypatch.setattr(BroadcastService, "_enqueue_broadcast", staticmethod(ok_enqueue))

    created = await client.post(BROADCAST_URL, headers=headers, json=_payload(audience="verified"))
    resp = await client.post(f"{BROADCAST_URL}/{created.json()['id']}/launch", headers=headers)

    assert resp.status_code == 200
    rows = (await db_session.execute(select(BroadcastRecipient))).scalars().all()
    assert len(rows) == 2
    assert all(row.user_id is not None for row in rows)


async def test_launch_allowed_only_for_draft(db_session, client, monkeypatch):
    headers = await _admin_headers(db_session)

    async def ok_enqueue(_: int) -> bool:
        return True

    monkeypatch.setattr(BroadcastService, "_enqueue_broadcast", staticmethod(ok_enqueue))

    created = await client.post(
        BROADCAST_URL, headers=headers, json=_payload(emails=["a@example.com"])
    )
    broadcast_id = created.json()["id"]
    await client.post(f"{BROADCAST_URL}/{broadcast_id}/launch", headers=headers)

    second = await client.post(f"{BROADCAST_URL}/{broadcast_id}/launch", headers=headers)

    assert second.status_code == 409


async def test_launch_rolls_back_when_queue_unavailable(db_session, client, monkeypatch):
    headers = await _admin_headers(db_session)

    async def fail_enqueue(_: int) -> bool:
        return False

    monkeypatch.setattr(BroadcastService, "_enqueue_broadcast", staticmethod(fail_enqueue))

    created = await client.post(
        BROADCAST_URL, headers=headers, json=_payload(emails=["a@example.com"])
    )
    broadcast_id = created.json()["id"]

    resp = await client.post(f"{BROADCAST_URL}/{broadcast_id}/launch", headers=headers)

    assert resp.status_code == 503
    broadcast = await _broadcast_by_id(db_session, broadcast_id)
    assert broadcast.status == BroadcastStatus.draft
    rows = (
        (
            await db_session.execute(
                select(BroadcastRecipient).where(BroadcastRecipient.broadcast_id == broadcast_id)
            )
        )
        .scalars()
        .all()
    )
    assert rows == []


async def test_cancel_cancels_active_broadcast(db_session, client):
    headers = await _admin_headers(db_session)
    broadcast = Broadcast(
        name="Active",
        audience="custom",
        subject="s",
        text="t",
        status=BroadcastStatus.running,
        total_recipients=3,
    )
    db_session.add(broadcast)
    await db_session.flush()

    resp = await client.post(f"{BROADCAST_URL}/{broadcast.id}/cancel", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


async def test_cancel_rejected_for_completed_broadcast(db_session, client):
    headers = await _admin_headers(db_session)
    broadcast = Broadcast(
        name="Done", audience="custom", subject="s", text="t", status=BroadcastStatus.completed
    )
    db_session.add(broadcast)
    await db_session.flush()

    resp = await client.post(f"{BROADCAST_URL}/{broadcast.id}/cancel", headers=headers)

    assert resp.status_code == 409


async def test_delete_removes_draft_but_not_active(db_session, client):
    headers = await _admin_headers(db_session)
    draft = Broadcast(name="Draft", audience="custom", subject="s", text="t")
    running = Broadcast(
        name="Running", audience="custom", subject="s", text="t", status=BroadcastStatus.running
    )
    db_session.add_all([draft, running])
    await db_session.flush()

    ok = await client.delete(f"{BROADCAST_URL}/{draft.id}", headers=headers)
    blocked = await client.delete(f"{BROADCAST_URL}/{running.id}", headers=headers)

    assert ok.status_code == 204
    assert blocked.status_code == 409
    assert await _broadcast_by_id(db_session, draft.id) is None
    assert await _broadcast_by_id(db_session, running.id) is not None


async def test_recipients_list_filters_by_status(db_session, client):
    headers = await _admin_headers(db_session)
    broadcast = Broadcast(name="B", audience="custom", subject="s", text="t")
    db_session.add(broadcast)
    await db_session.flush()
    db_session.add_all(
        [
            BroadcastRecipient(broadcast_id=broadcast.id, email="s@example.com", status="sent"),
            BroadcastRecipient(broadcast_id=broadcast.id, email="f@example.com", status="failed"),
            BroadcastRecipient(broadcast_id=broadcast.id, email="p@example.com", status="pending"),
        ]
    )
    await db_session.flush()

    all_rows = await client.get(f"{BROADCAST_URL}/{broadcast.id}/recipients", headers=headers)
    sent_rows = await client.get(
        f"{BROADCAST_URL}/{broadcast.id}/recipients?status=sent", headers=headers
    )

    assert all_rows.json()["total"] == 3
    assert sent_rows.json()["total"] == 1
    assert sent_rows.json()["items"][0]["email"] == "s@example.com"


async def test_non_admin_gets_403(db_session, client):
    plain = await _make_user(db_session, "plain@example.com", is_admin=False)
    headers = _auth(create_access_token(plain.id))

    resp = await client.get(BROADCAST_URL, headers=headers)

    assert resp.status_code == 403


async def test_send_test_delivers_to_admin_by_default(db_session, client, monkeypatch):
    headers = await _admin_headers(db_session)
    fake = FakeMailer()
    monkeypatch.setattr("src.modules.broadcast.service.broadcast_service.get_mailer", lambda: fake)

    created = await client.post(
        BROADCAST_URL, headers=headers, json=_payload(emails=["a@example.com"])
    )
    broadcast_id = created.json()["id"]

    resp = await client.post(f"{BROADCAST_URL}/{broadcast_id}/send-test", headers=headers, json={})

    assert resp.status_code == 200
    assert resp.json()["sent_to"] == "badmin@example.com"
    assert fake.sent[0][0] == "badmin@example.com"


async def test_run_job_completes_and_marks_recipients_sent(db_session, monkeypatch):
    fake = FakeMailer()
    monkeypatch.setattr("src.modules.broadcast.service.broadcast_service.get_mailer", lambda: fake)
    monkeypatch.setattr(settings, "broadcast_send_delay_seconds", 0.0)

    broadcast = Broadcast(
        name="Job",
        audience="custom",
        subject="Тема",
        text="Тело",
        status=BroadcastStatus.queued,
        total_recipients=2,
    )
    db_session.add(broadcast)
    await db_session.flush()
    db_session.add_all(
        [
            BroadcastRecipient(broadcast_id=broadcast.id, email="a@example.com"),
            BroadcastRecipient(broadcast_id=broadcast.id, email="b@example.com"),
        ]
    )
    await db_session.commit()

    result = await BroadcastService.run_broadcast_job(broadcast.id, db=db_session)

    assert result["status"] == "completed"
    assert sorted(email for email, _, _ in fake.sent) == ["a@example.com", "b@example.com"]
    rows = (
        (
            await db_session.execute(
                select(BroadcastRecipient).where(BroadcastRecipient.broadcast_id == broadcast.id)
            )
        )
        .scalars()
        .all()
    )
    assert all(row.status == RecipientStatus.sent for row in rows)
    assert broadcast.sent_count == 2


async def test_run_job_skips_cancelled_broadcast(db_session, monkeypatch):
    fake = FakeMailer()
    monkeypatch.setattr("src.modules.broadcast.service.broadcast_service.get_mailer", lambda: fake)
    broadcast = Broadcast(
        name="Cancelled",
        audience="custom",
        subject="s",
        text="t",
        status=BroadcastStatus.cancelled,
    )
    db_session.add(broadcast)
    await db_session.flush()

    result = await BroadcastService.run_broadcast_job(broadcast.id, db=db_session)

    assert result["status"] == "skipped"
    assert fake.sent == []


async def test_run_job_tracks_failed_deliveries(db_session, monkeypatch):
    class ExplodingMailer:
        async def send(self, to: str, subject: str, text: str, html: str | None = None) -> None:
            raise RuntimeError("smtp exploded")

    monkeypatch.setattr(
        "src.modules.broadcast.service.broadcast_service.get_mailer", lambda: ExplodingMailer()
    )
    monkeypatch.setattr(settings, "broadcast_send_delay_seconds", 0.0)

    broadcast = Broadcast(
        name="Fail",
        audience="custom",
        subject="s",
        text="t",
        status=BroadcastStatus.queued,
        total_recipients=1,
    )
    db_session.add(broadcast)
    await db_session.flush()
    db_session.add(BroadcastRecipient(broadcast_id=broadcast.id, email="a@example.com"))
    await db_session.commit()

    result = await BroadcastService.run_broadcast_job(broadcast.id, db=db_session)

    assert result["status"] == "completed"
    assert broadcast.failed_count == 1
    row = (
        await db_session.execute(
            select(BroadcastRecipient).where(BroadcastRecipient.broadcast_id == broadcast.id)
        )
    ).scalar_one()
    assert row.status == RecipientStatus.failed
    assert "smtp exploded" in row.error


async def test_broadcast_list_is_paginated(db_session, client):
    headers = await _admin_headers(db_session)
    for index in range(3):
        db_session.add(Broadcast(name=f"B{index}", audience="custom", subject="s", text="t"))
    await db_session.flush()

    first = await client.get(f"{BROADCAST_URL}?page=1&per_page=2", headers=headers)
    second = await client.get(f"{BROADCAST_URL}?page=2&per_page=2", headers=headers)

    assert first.json()["total"] == 3
    assert len(first.json()["items"]) == 2
    assert len(second.json()["items"]) == 1
