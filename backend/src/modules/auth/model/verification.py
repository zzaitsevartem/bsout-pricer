from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

TOKEN_PURPOSES = ("password_reset", "email_verify")
IDENTITY_PROVIDERS = ("vk", "telegram")


class VerificationToken(Base):
    __tablename__ = "verification_tokens"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('password_reset', 'email_verify')", name="verification_purpose_allowed"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purpose: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")  # noqa: F821


class UserIdentity(Base):
    __tablename__ = "user_identities"
    __table_args__ = (
        CheckConstraint("provider IN ('vk', 'telegram')", name="identity_provider_allowed"),
        UniqueConstraint("provider", "provider_user_id", name="uq_identity_provider_user"),
        UniqueConstraint("user_id", "provider", name="uq_identity_user_provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")  # noqa: F821
