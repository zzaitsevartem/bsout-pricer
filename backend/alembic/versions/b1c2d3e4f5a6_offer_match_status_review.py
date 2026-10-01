"""offer match_status review

Revision ID: b1c2d3e4f5a6
Revises: 850c458e9790
Create Date: 2026-07-26 11:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "850c458e9790"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT = "ck_store_offers_match_status_allowed"


def upgrade() -> None:
    op.execute(f"ALTER TABLE store_offers DROP CONSTRAINT {CONSTRAINT}")
    op.execute(
        f"ALTER TABLE store_offers ADD CONSTRAINT {CONSTRAINT} "
        "CHECK (match_status IN ('unmatched', 'auto', 'manual', 'rejected', 'review'))"
    )


def downgrade() -> None:
    op.execute("UPDATE store_offers SET match_status = 'unmatched' WHERE match_status = 'review'")
    op.execute(f"ALTER TABLE store_offers DROP CONSTRAINT {CONSTRAINT}")
    op.execute(
        f"ALTER TABLE store_offers ADD CONSTRAINT {CONSTRAINT} "
        "CHECK (match_status IN ('unmatched', 'auto', 'manual', 'rejected'))"
    )
