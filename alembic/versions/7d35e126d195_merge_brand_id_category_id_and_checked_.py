"""merge brand_id category_id and checked_at nullable migrations

Revision ID: 7d35e126d195
Revises: 1793a2b8523d, c18730160b0c
Create Date: 2026-01-25 06:46:37.383887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d35e126d195'
down_revision: Union[str, None] = ('1793a2b8523d', 'c18730160b0c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
