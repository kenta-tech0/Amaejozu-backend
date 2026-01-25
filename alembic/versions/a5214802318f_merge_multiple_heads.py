"""merge multiple heads

Revision ID: a5214802318f
Revises: 1793a2b8523d, c18730160b0c
Create Date: 2026-01-25 12:32:19.697630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5214802318f'
down_revision: Union[str, None] = ('1793a2b8523d', 'c18730160b0c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
