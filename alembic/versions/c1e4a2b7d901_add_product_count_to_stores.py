"""add product_count to stores

Revision ID: c1e4a2b7d901
Revises: 9b7f6d8c1234
Create Date: 2026-02-28 00:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1e4a2b7d901"
down_revision: Union[str, Sequence[str], None] = "9b7f6d8c1234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "stores",
        sa.Column("product_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("stores", "product_count", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("stores", "product_count")
