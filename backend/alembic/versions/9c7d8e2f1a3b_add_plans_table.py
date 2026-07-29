from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "9c7d8e2f1a3b"
down_revision: Union[str, None] = "b8a3e09670ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("price", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("period", sa.String(50), nullable=False),
        sa.Column("discount", sa.String(255), nullable=True),
        sa.Column("featured", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("features", JSON, nullable=False),
        sa.Column("tooltips", JSON, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plans_slug", "plans", ["slug"], unique=True)

    op.execute(
        sa.table(
            "plans",
            sa.column("slug", sa.String),
            sa.column("name", sa.String),
            sa.column("price", sa.DECIMAL),
            sa.column("period", sa.String),
            sa.column("discount", sa.String),
            sa.column("featured", sa.Boolean),
            sa.column("features", JSON),
            sa.column("tooltips", JSON),
            sa.column("is_active", sa.Boolean),
        ).insert().values(
            slug="trial",
            name="Пробный",
            price=0,
            period="/ 7 дней",
            discount="Бесплатно",
            featured=False,
            features=sa.text("'[\"Все 5 магазинов\", \"Точный + частичный поиск\", \"До 10 товаров\", \"История цен — 3 месяца\"]'::jsonb"),
            tooltips=sa.text("'[\"Точное + частичное совпадение\", \"До 10 отслеживаемых товаров\", \"История цен — 3 месяца\", \"7 дней бесплатного доступа\", \"После окончания — автоматическое продление\"]'::jsonb"),
            is_active=True,
        )
    )

    op.execute(
        sa.table(
            "plans",
            sa.column("slug", sa.String),
            sa.column("name", sa.String),
            sa.column("price", sa.DECIMAL),
            sa.column("period", sa.String),
            sa.column("discount", sa.String),
            sa.column("featured", sa.Boolean),
            sa.column("features", JSON),
            sa.column("tooltips", JSON),
            sa.column("is_active", sa.Boolean),
        ).insert().values(
            slug="basic",
            name="Базовый",
            price=399,
            period="/ месяц",
            discount="−20% на первый платёж",
            featured=False,
            features=sa.text("'[\"Все 5 магазинов\", \"Точный + частичный поиск\", \"До 100 товаров\", \"История цен — 3 месяца\"]'::jsonb"),
            tooltips=sa.text("'[\"Точное + частичное совпадение\", \"До 100 отслеживаемых товаров\", \"История цен — 3 месяца\", \"Без уведомлений о падении цен\", \"Без экспорта отчётов\", \"Поддержка в рабочие часы\"]'::jsonb"),
            is_active=True,
        )
    )

    op.execute(
        sa.table(
            "plans",
            sa.column("slug", sa.String),
            sa.column("name", sa.String),
            sa.column("price", sa.DECIMAL),
            sa.column("period", sa.String),
            sa.column("discount", sa.String),
            sa.column("featured", sa.Boolean),
            sa.column("features", JSON),
            sa.column("tooltips", JSON),
            sa.column("is_active", sa.Boolean),
        ).insert().values(
            slug="advanced",
            name="Продвинутый",
            price=499,
            period="/ месяц",
            discount="−20% на первый платёж",
            featured=True,
            features=sa.text("'[\"Все 5 магазинов\", \"Умный поиск (fuzzy)\", \"До 500 товаров\", \"Уведомления о снижении цен\", \"Экспорт PDF/CSV\", \"Поддержка 24/7\"]'::jsonb"),
            tooltips=sa.text("'[\"Умный поиск (fuzzy) — находит при опечатках, транслитерации, другой раскладке\", \"До 500 отслеживаемых товаров\", \"Уведомления о снижении цен\", \"Экспорт отчётов PDF/CSV\", \"Поддержка 24/7\"]'::jsonb"),
            is_active=True,
        )
    )


def downgrade() -> None:
    op.drop_table("plans")
