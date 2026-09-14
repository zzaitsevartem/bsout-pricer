"""add username login field

Revision ID: c356386a2cd0
Revises: ca1001d72baa
Create Date: 2026-09-08 23:53:31.164869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c356386a2cd0'
down_revision: Union[str, None] = 'ca1001d72baa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'username',
            postgresql.CITEXT(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_username', table_name='users')
    op.drop_column('users', 'username')
