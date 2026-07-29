from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy import DECIMAL as SA_DECIMAL
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Decimal] = mapped_column(SA_DECIMAL(10, 2), nullable=False)
    period: Mapped[str] = mapped_column(String(50), nullable=False)
    discount: Mapped[str | None] = mapped_column(String(255), nullable=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    features: Mapped[list] = mapped_column(JSON, nullable=False)
    tooltips: Mapped[list] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Plan {self.id}: {self.slug}>"
