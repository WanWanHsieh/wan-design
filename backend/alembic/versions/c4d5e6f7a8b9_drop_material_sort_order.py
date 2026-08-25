"""drop materials.sort_order — manual per-material priority was unused and removed

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('materials', 'sort_order')


def downgrade() -> None:
    op.add_column('materials', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('materials', 'sort_order', server_default=None)
