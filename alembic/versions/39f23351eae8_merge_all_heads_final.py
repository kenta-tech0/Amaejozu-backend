"""merge all heads final

Revision ID: 39f23351eae8
Revises: 6beb10e05c8c, c7ebe54096c0, f797a27fa55f
Create Date: 2026-01-26 15:11:39.085811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39f23351eae8'
down_revision: Union[str, None] = ('6beb10e05c8c', 'c7ebe54096c0', 'f797a27fa55f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
