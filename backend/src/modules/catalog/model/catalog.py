from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    devices: Mapped[list["Device"]] = relationship(
        "Device", back_populates="brand", cascade="all, delete-orphan"
    )


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    model_key: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    brand: Mapped["Brand"] = relationship("Brand", back_populates="devices")
    aliases: Mapped[list["DeviceAlias"]] = relationship(
        "DeviceAlias", back_populates="device", cascade="all, delete-orphan"
    )


class DeviceAlias(Base):
    __tablename__ = "device_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    device: Mapped["Device"] = relationship("Device", back_populates="aliases")


class PartType(Base):
    __tablename__ = "part_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name_ru: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    synonyms: Mapped[list["PartTypeSynonym"]] = relationship(
        "PartTypeSynonym", back_populates="part_type", cascade="all, delete-orphan"
    )


class PartTypeSynonym(Base):
    __tablename__ = "part_type_synonyms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_type_id: Mapped[int] = mapped_column(
        ForeignKey("part_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    synonym: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)

    part_type: Mapped["PartType"] = relationship("PartType", back_populates="synonyms")


class QualityTier(Base):
    __tablename__ = "quality_tiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name_ru: Mapped[str] = mapped_column(String(120), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    synonyms: Mapped[list["QualityTierSynonym"]] = relationship(
        "QualityTierSynonym", back_populates="quality_tier", cascade="all, delete-orphan"
    )


class QualityTierSynonym(Base):
    __tablename__ = "quality_tier_synonyms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quality_tier_id: Mapped[int] = mapped_column(
        ForeignKey("quality_tiers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    synonym: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)

    quality_tier: Mapped["QualityTier"] = relationship("QualityTier", back_populates="synonyms")


class Color(Base):
    __tablename__ = "colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name_ru: Mapped[str] = mapped_column(String(120), nullable=False)


class ColorSynonym(Base):
    __tablename__ = "color_synonyms"
    __table_args__ = (UniqueConstraint("synonym", name="uq_color_synonyms_synonym"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    color_id: Mapped[int] = mapped_column(
        ForeignKey("colors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    synonym: Mapped[str] = mapped_column(CITEXT, nullable=False)

    color: Mapped["Color"] = relationship("Color")


class Stopword(Base):
    __tablename__ = "stopwords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(CITEXT, nullable=False, unique=True)
