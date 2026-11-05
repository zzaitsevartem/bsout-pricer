"""device sourced metadata

Revision ID: 077299b69ec0
Revises: 6a307de976b1
Create Date: 2026-11-05 13:12:16.729850

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "077299b69ec0"
down_revision: Union[str, None] = "6a307de976b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("release_year", sa.Integer(), nullable=True))
    op.add_column(
        "devices", sa.Column("model_codes", sa.JSON(), server_default="[]", nullable=False)
    )
    op.add_column("devices", sa.Column("images", sa.JSON(), server_default="[]", nullable=False))
    op.add_column(
        "devices", sa.Column("metadata_source_url", sa.String(length=2000), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("devices", "metadata_source_url")
    op.drop_column("devices", "images")
    op.drop_column("devices", "model_codes")
    op.drop_column("devices", "release_year")
