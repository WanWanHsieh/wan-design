"""add orders.real_name and orders.contact_source

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('real_name', sa.String(100), nullable=True))
    op.add_column('orders', sa.Column('contact_source', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'contact_source')
    op.drop_column('orders', 'real_name')
