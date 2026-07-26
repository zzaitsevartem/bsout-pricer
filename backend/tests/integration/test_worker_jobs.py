from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from src.modules.auth.model.refresh_token import RefreshToken
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.auth import hash_password
from src.worker import WorkerSettings, cleanup_refresh_tokens, expire_subscriptions

pytestmark = pytest.mark.integration


async def _user(db, email: str) -> User:
    user = User(
        email=email, password_hash=hash_password("s3cret-pass"), full_name="W", is_active=True
    )
    db.add(user)
    await db.flush()
    return user


async def test_expire_subscriptions_deactivates_only_finished_ones(db_session):
    user = await _user(db_session, "expire-job@example.com")
    now = datetime.now(timezone.utc)
    db_session.add(
        Subscription(
            user_id=user.id,
            plan=PlanEnum.basic,
            start_date=now - timedelta(days=40),
            end_date=now - timedelta(days=10),
            is_active=True,
        )
    )
    db_session.add(
        Subscription(
            user_id=user.id,
            plan=PlanEnum.advanced,
            start_date=now,
            end_date=now + timedelta(days=20),
            is_active=True,
        )
    )
    await db_session.commit()

    await expire_subscriptions(None, db=db_session)

    stale = (
        await db_session.execute(
            select(func.count())
            .select_from(Subscription)
            .where(
                Subscription.user_id == user.id,
                Subscription.is_active.is_(True),
                Subscription.end_date < datetime.now(timezone.utc),
            )
        )
    ).scalar()
    alive = (
        await db_session.execute(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
        )
    ).scalar()

    assert stale == 0
    assert alive == 1


async def test_cleanup_removes_expired_and_revoked_but_keeps_live_tokens(db_session):
    user = await _user(db_session, "cleanup-job@example.com")
    now = datetime.now(timezone.utc)
    db_session.add(
        RefreshToken(
            jti="j-expired", family_id="f1", user_id=user.id, expires_at=now - timedelta(days=1)
        )
    )
    db_session.add(
        RefreshToken(
            jti="j-revoked",
            family_id="f2",
            user_id=user.id,
            expires_at=now + timedelta(days=10),
            revoked_at=now,
            revoked_reason="logout",
        )
    )
    db_session.add(
        RefreshToken(
            jti="j-live", family_id="f3", user_id=user.id, expires_at=now + timedelta(days=10)
        )
    )
    await db_session.commit()

    await cleanup_refresh_tokens(None, db=db_session)

    left = (
        (await db_session.execute(select(RefreshToken.jti).where(RefreshToken.user_id == user.id)))
        .scalars()
        .all()
    )

    assert left == ["j-live"]


def test_worker_schedule_does_not_crawl_stores_more_than_once_a_day():
    catalog_crons = [c for c in WorkerSettings.cron_jobs if "sync_catalog" in c.name]

    assert len(catalog_crons) == 1
    assert catalog_crons[0].hour == 3
