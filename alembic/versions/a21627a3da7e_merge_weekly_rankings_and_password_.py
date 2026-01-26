"""merge weekly_rankings and password_reset_email_unique heads

Revision ID: a21627a3da7e
Revises: 6beb10e05c8c, c7ebe54096c0
Create Date: 2026-01-26 14:56:12.239333

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a21627a3da7e'
down_revision: Union[str, None] = ('6beb10e05c8c', 'c7ebe54096c0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
