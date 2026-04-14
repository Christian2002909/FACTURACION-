"""add_stock_to_producto

Revision ID: 289df8084b86
Revises: 4c126f914711
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '289df8084b86'
down_revision: Union[str, None] = '4c126f914711'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('producto', sa.Column('stock', sa.Numeric(precision=10, scale=3), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('producto', 'stock')
