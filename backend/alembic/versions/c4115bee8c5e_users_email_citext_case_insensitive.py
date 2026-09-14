"""users email citext case insensitive

Revision ID: c4115bee8c5e
Revises: 336d8cc4267a
Create Date: 2026-07-25 14:00:35.965370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4115bee8c5e'
down_revision: Union[str, None] = '336d8cc4267a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("ALTER TABLE users ALTER COLUMN email TYPE citext")


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN email TYPE VARCHAR(255)")
