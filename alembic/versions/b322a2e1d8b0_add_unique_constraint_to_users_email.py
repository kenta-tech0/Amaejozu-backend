"""add unique constraint to users email

Revision ID: b322a2e1d8b0
Revises: 488350b719ed
Create Date: 2026-01-25 13:51:40.128933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b322a2e1d8b0'
down_revision: Union[str, None] = '488350b719ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 既存のインデックスを削除
    op.drop_index('ix_users_email', table_name='users')
    # ユニーク制約付きインデックスを作成
    op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    # ユニーク制約付きインデックスを削除
    op.drop_index('ix_users_email', table_name='users')
    # 通常のインデックスを作成
    op.create_index('ix_users_email', 'users', ['email'], unique=False)