"""add product image type field

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0f1a2b3c4d5'
down_revision: Union[str, None] = 'd9e0f1a2b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'product_images',
        sa.Column('image_type', sa.String(20), nullable=False, server_default='main'),
    )
    op.alter_column('product_images', 'image_type', server_default=None)


def downgrade() -> None:
    op.drop_column('product_images', 'image_type')
