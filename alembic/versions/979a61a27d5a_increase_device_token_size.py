"""increase_device_token_size

Revision ID: 979a61a27d5a
Revises: b72cf568c592
Create Date: 2026-01-27 14:48:39.046595

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '979a61a27d5a'
down_revision: Union[str, None] = 'b72cf568c592'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'users',
        'device_token',
        existing_type=sa.String(255),
        type_=sa.String(1024),
        existing_nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        'users',
        'device_token',
        existing_type=sa.String(1024),
        type_=sa.String(255),
        existing_nullable=True
    )
