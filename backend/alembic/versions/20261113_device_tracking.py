"""Add device tracking and new-product notifications."""

import sqlalchemy as sa
from alembic import op

revision = "20261113_device_tracking"
down_revision = "077299b69ec0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tracked_devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "device_id",
            sa.Integer(),
            sa.ForeignKey("devices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", "device_id", name="uq_tracked_user_device"),
    )
    op.create_table(
        "tracked_device_products",
        sa.Column(
            "tracked_device_id",
            sa.Integer(),
            sa.ForeignKey("tracked_devices.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.drop_constraint(op.f("ck_notifications_type_allowed"), "notifications", type_="check")
    op.create_check_constraint(
        op.f("ck_notifications_type_allowed"),
        "notifications",
        "type IN ('price_drop', 'back_in_stock', 'target_reached', 'new_device_product')",
    )


def downgrade():
    op.execute("DELETE FROM notifications WHERE type = 'new_device_product'")
    op.drop_constraint(op.f("ck_notifications_type_allowed"), "notifications", type_="check")
    op.create_check_constraint(
        op.f("ck_notifications_type_allowed"),
        "notifications",
        "type IN ('price_drop', 'back_in_stock', 'target_reached')",
    )
    op.drop_table("tracked_device_products")
    op.drop_table("tracked_devices")
