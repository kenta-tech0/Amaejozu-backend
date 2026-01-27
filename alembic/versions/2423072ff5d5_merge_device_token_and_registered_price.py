"""merge_device_token_and_registered_price

Revision ID: 2423072ff5d5
Revises: 1c950e9b82a0, 979a61a27d5a
Create Date: 2026-01-27 15:10:44.255342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2423072ff5d5'
down_revision: Union[str, None] = ('1c950e9b82a0', '979a61a27d5a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
