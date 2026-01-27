"""add_registered_price_to_watchlist

Revision ID: 1c950e9b82a0
Revises: b72cf568c592
Create Date: 2026-01-27 13:18:17.672391

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c950e9b82a0'
down_revision: Union[str, None] = 'b72cf568c592'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('watchlists', sa.Column('registered_price', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('watchlists', 'registered_price')
