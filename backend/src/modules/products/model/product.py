from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Decimal as SA_Decimal, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False)
    old_price: Mapped[Decimal | None] = mapped_column(SA_Decimal(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="RUB", nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    product_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    price_history: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan", order_by="PriceHistory.recorded_at"
    )

    def __repr__(self) -> str:
        return f"<Product {self.id}: {self.name}>"


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="price_history")
