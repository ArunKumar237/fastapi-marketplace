"""create cart items table

Revision ID: b2f4a6c8d9e1
Revises: a3b7d1f4c9e2
Create Date: 2026-03-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2f4a6c8d9e1"
down_revision: Union[str, Sequence[str], None] = "a3b7d1f4c9e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cart_items",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name="ck_cart_items_quantity_gt_0"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_cart_items_user_product"),
    )
    op.create_index(op.f("ix_cart_items_user_id"), "cart_items", ["user_id"], unique=False)
    op.alter_column("cart_items", "quantity", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_cart_items_user_id"), table_name="cart_items")
    op.drop_table("cart_items")
