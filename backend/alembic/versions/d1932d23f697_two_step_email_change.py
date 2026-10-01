"""two_step_email_change

Revision ID: d1932d23f697
Revises: 97c07d54808c
Create Date: 2026-09-02 22:42:22.054112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd1932d23f697'
down_revision: Union[str, None] = '97c07d54808c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PURPOSE_CONSTRAINT = 'ck_verification_tokens_verification_purpose_allowed'
_OLD_CHECK = (
    "purpose IN ('password_reset', 'email_verify', 'email_change')"
)
_NEW_CHECK = (
    "purpose IN ('password_reset', 'email_verify', 'email_change', "
    "'email_change_old', 'email_change_new', 'email_change_freeze')"
)


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('email_change_old_confirmed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(f"ALTER TABLE verification_tokens DROP CONSTRAINT {_PURPOSE_CONSTRAINT}")
    op.execute(
        f"ALTER TABLE verification_tokens ADD CONSTRAINT {_PURPOSE_CONSTRAINT} "
        f"CHECK ({_NEW_CHECK})"
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE verification_tokens DROP CONSTRAINT {_PURPOSE_CONSTRAINT}")
    op.execute(
        f"ALTER TABLE verification_tokens ADD CONSTRAINT {_PURPOSE_CONSTRAINT} "
        f"CHECK ({_OLD_CHECK})"
    )
    op.drop_column('users', 'email_change_old_confirmed_at')
