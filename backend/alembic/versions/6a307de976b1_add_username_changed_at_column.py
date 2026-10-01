"""add username changed at column

Revision ID: 6a307de976b1
Revises: c356386a2cd0
Create Date: 2026-09-09 00:21:47.349193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '6a307de976b1'
down_revision: Union[str, None] = 'c356386a2cd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'username_changed_at',
            sa.DateTime(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'username_changed_at')
