"""Add unique and on conflict to upd

Revision ID: a6cb6f38c3cb
Revises: 7f9526b84663
Create Date: 2025-06-03 12:48:21.851746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6cb6f38c3cb'
down_revision: Union[str, None] = '7f9526b84663'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_user_balance_change_nonce_model_balance_id', table_name='user_balance_change_nonce_model')
    op.create_index(
        'ix_user_balance_change_nonce_model_balance_id',
        'user_balance_change_nonce_model',
        ['balance_id'],
        unique=True,
        postgresql_using='btree'
    )


def downgrade() -> None:
    op.drop_index('ix_user_balance_change_nonce_model_balance_id', table_name='user_balance_change_nonce_model')
    op.create_index(
        'ix_user_balance_change_nonce_model_balance_id',
        'user_balance_change_nonce_model',
        ['balance_id'],
        unique=False,
        postgresql_using='btree'
    )

