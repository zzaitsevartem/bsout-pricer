"""add user pending_email and email_change purpose

Revision ID: 97c07d54808c
Revises: b1c2d3e4f5a6
Create Date: 2026-09-02 21:57:00.713898

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '97c07d54808c'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PURPOSE_CONSTRAINT = 'ck_verification_tokens_verification_purpose_allowed'
_OLD_CHECK = "purpose IN ('password_reset', 'email_verify')"
_NEW_CHECK = "purpose IN ('password_reset', 'email_verify', 'email_change')"


def upgrade() -> None:
    op.add_column('users', sa.Column('pending_email', postgresql.CITEXT(), nullable=True))
    op.execute(
        f"ALTER TABLE verification_tokens DROP CONSTRAINT {_PURPOSE_CONSTRAINT}"
    )
    op.execute(
        f"ALTER TABLE verification_tokens ADD CONSTRAINT {_PURPOSE_CONSTRAINT} "
        f"CHECK ({_NEW_CHECK})"
    )


def downgrade() -> None:
    op.execute(
        f"ALTER TABLE verification_tokens DROP CONSTRAINT {_PURPOSE_CONSTRAINT}"
    )
    op.execute(
        f"ALTER TABLE verification_tokens ADD CONSTRAINT {_PURPOSE_CONSTRAINT} "
        f"CHECK ({_OLD_CHECK})"
    )
    op.drop_column('users', 'pending_email')
