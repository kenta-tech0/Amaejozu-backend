"""merge all remaining heads

Revision ID: b72cf568c592
Revises: fa04fa27bfc5, 6beb10e05c8c
Create Date: 2026-01-26 15:12:41.730353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b72cf568c592'
down_revision: Union[str, None] = ('fa04fa27bfc5', '6beb10e05c8c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
