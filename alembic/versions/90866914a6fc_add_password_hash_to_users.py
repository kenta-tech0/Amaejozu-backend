"""add password_hash to users

Revision ID: 90866914a6fc
Revises: 372441cddb3f
Create Date: 2026-01-19 08:00:14.183572

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "90866914a6fc"
down_revision: Union[str, Sequence[str], None] = "de571193d02e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "password_hash")
