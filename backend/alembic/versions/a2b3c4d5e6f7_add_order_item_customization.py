"""add order/order-item custom note and price adjustment fields

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('adjustment_amount', sa.Numeric(12, 2), nullable=False, server_default='0'))
    op.alter_column('orders', 'adjustment_amount', server_default=None)
    op.add_column('orders', sa.Column('adjustment_note', sa.Text(), nullable=True))

    op.add_column('order_items', sa.Column('custom_note', sa.Text(), nullable=True))
    op.add_column('order_items', sa.Column('extra_charge', sa.Numeric(12, 2), nullable=False, server_default='0'))
    op.alter_column('order_items', 'extra_charge', server_default=None)


def downgrade() -> None:
    op.drop_column('order_items', 'extra_charge')
    op.drop_column('order_items', 'custom_note')
    op.drop_column('orders', 'adjustment_note')
    op.drop_column('orders', 'adjustment_amount')
