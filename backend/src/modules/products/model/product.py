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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

STOCK_STATUSES = ("in_stock", "low", "out", "preorder", "unknown")
OFFER_MATCH_STATUSES = ("unmatched", "auto", "manual", "rejected", "review")
CANDIDATE_STATUSES = ("pending", "approved", "rejected")


class Cluster(Base):
    __tablename__ = "clusters"
    __table_args__ = (UniqueConstraint("device_id", "part_type_id", name="uq_clusters_device_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    part_type_id: Mapped[int] = mapped_column(
        ForeignKey("part_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    offers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_price_retail: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    min_price_opt: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    products: Mapped[list["Product"]] = relationship("Product", back_populates="cluster")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cluster_id: Mapped[int | None] = mapped_column(
        ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    quality_tier_id: Mapped[int | None] = mapped_column(
        ForeignKey("quality_tiers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    brand_id: Mapped[int | None] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True
    )
    key_attrs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    canonical_key: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cluster: Mapped["Cluster | None"] = relationship("Cluster", back_populates="products")
    offers: Mapped[list["StoreOffer"]] = relationship("StoreOffer", back_populates="product")


class StoreOffer(Base):
    __tablename__ = "store_offers"
    __table_args__ = (
        UniqueConstraint("store_id", "source_sku", name="uq_store_offers_store_id"),
        CheckConstraint(
            "stock_status IN ('in_stock', 'low', 'out', 'preorder', 'unknown')",
            name="stock_status_allowed",
        ),
        CheckConstraint(
            "match_status IN ('unmatched', 'auto', 'manual', 'rejected', 'review')",
            name="match_status_allowed",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_sku: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price_retail: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_opt: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_old: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="RUB", nullable=False)
    stock_status: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    stock_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    match_status: Mapped[str] = mapped_column(String(20), default="unmatched", nullable=False)
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    price_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product | None"] = relationship("Product", back_populates="offers")
    price_history: Mapped[list["OfferPriceHistory"]] = relationship(
        "OfferPriceHistory",
        back_populates="offer",
        cascade="all, delete-orphan",
        order_by="OfferPriceHistory.recorded_at",
    )

    def __repr__(self) -> str:
        return f"<StoreOffer {self.id}: {self.title}>"


class OfferPriceHistory(Base):
    __tablename__ = "offer_price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(
        ForeignKey("store_offers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price_retail: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_opt: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    stock_status: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    offer: Mapped["StoreOffer"] = relationship("StoreOffer", back_populates="price_history")


class MatchCandidate(Base):
    __tablename__ = "match_candidates"
    __table_args__ = (
        UniqueConstraint("offer_id", "product_id", name="uq_match_candidates_offer_id"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="status_allowed",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(
        ForeignKey("store_offers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    decided_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
