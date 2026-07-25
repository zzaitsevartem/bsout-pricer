from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

NOTIFICATION_TYPES = ("price_drop", "back_in_stock", "target_reached")
NOTIFICATION_CHANNELS = ("in_app", "email", "telegram")
NOTIFICATION_STATUSES = ("pending", "sent", "failed", "skipped")


class TrackedProduct(Base):
    __tablename__ = "tracked_products"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_tracked_user_product"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    notify_on_any_drop: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")  # noqa: F821
    product: Mapped["Product"] = relationship("Product")  # noqa: F821


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "type IN ('price_drop', 'back_in_stock', 'target_reached')", name="type_allowed"
        ),
        CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'skipped')", name="notification_status_allowed"
        ),
        UniqueConstraint("dedup_key", name="uq_notification_dedup_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tracked_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("tracked_products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="in_app", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(String(1000), nullable=False)
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    new_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    dedup_key: Mapped[str] = mapped_column(String(200), nullable=False)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
