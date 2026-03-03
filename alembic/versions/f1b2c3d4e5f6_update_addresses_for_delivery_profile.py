"""update addresses for delivery profile

Revision ID: f1b2c3d4e5f6
Revises: e8f2a4b6c1d3
Create Date: 2026-03-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e8f2a4b6c1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "addresses",
        sa.Column(
            "label",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'Home'"),
        ),
    )
    op.alter_column("addresses", "label", server_default=None)
    op.alter_column("addresses", "line1", new_column_name="address_line_1")
    op.alter_column("addresses", "line2", new_column_name="address_line_2")
    op.alter_column("addresses", "country", type_=sa.String(length=50))


def downgrade() -> None:
    op.alter_column("addresses", "country", type_=sa.String(length=100))
    op.alter_column("addresses", "address_line_2", new_column_name="line2")
    op.alter_column("addresses", "address_line_1", new_column_name="line1")
    op.drop_column("addresses", "label")
