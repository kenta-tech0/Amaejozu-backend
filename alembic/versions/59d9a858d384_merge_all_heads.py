"""merge all heads

Revision ID: 59d9a858d384
Revises: 7d35e126d195, a5214802318f
Create Date: 2026-01-25 12:46:23.404347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59d9a858d384'
down_revision: Union[str, None] = ('7d35e126d195', 'a5214802318f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
