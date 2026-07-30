"""add product stock fields, allow order item without material

Revision ID: a1b2c3d4e5f6
Revises: 12751bdd14f2
Create Date: 2026-07-29 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '12751bdd14f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'products',
        sa.Column('track_stock', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'products',
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
    )
    op.alter_column('products', 'track_stock', server_default=None)
    op.alter_column('products', 'stock_quantity', server_default=None)

    op.alter_column('order_items', 'material_id', nullable=True)
    op.alter_column('order_items', 'material_name_snapshot', nullable=True)


def downgrade() -> None:
    op.alter_column('order_items', 'material_name_snapshot', nullable=False)
    op.alter_column('order_items', 'material_id', nullable=False)
    op.drop_column('products', 'stock_quantity')
    op.drop_column('products', 'track_stock')
