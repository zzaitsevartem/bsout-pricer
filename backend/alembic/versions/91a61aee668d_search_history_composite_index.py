"""search history composite index

Revision ID: 91a61aee668d
Revises: c4115bee8c5e
Create Date: 2026-07-25 14:25:06.060932

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '91a61aee668d'
down_revision: Union[str, None] = 'c4115bee8c5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_search_history_user_id_created_at',
        'search_history',
        ['user_id', sa.text('created_at DESC')],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_search_history_user_id_created_at', table_name='search_history')
