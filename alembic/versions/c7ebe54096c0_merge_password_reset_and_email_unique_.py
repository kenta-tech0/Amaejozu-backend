"""merge password_reset and email_unique heads

Revision ID: c7ebe54096c0
Revises: a1b2c3d4e5f6, b322a2e1d8b0
Create Date: 2026-01-26 14:42:00.990542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7ebe54096c0'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'b322a2e1d8b0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
