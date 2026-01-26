"""merge nullable migrations

Revision ID: fa04fa27bfc5
Revises: 1793a2b8523d, c18730160b0c
Create Date: 2026-01-26 15:12:33.746575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa04fa27bfc5'
down_revision: Union[str, None] = ('1793a2b8523d', 'c18730160b0c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
