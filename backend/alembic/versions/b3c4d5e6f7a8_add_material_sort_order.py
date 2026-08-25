"""add materials.sort_order for admin-controlled display ordering

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('materials', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('materials', 'sort_order', server_default=None)


def downgrade() -> None:
    op.drop_column('materials', 'sort_order')
