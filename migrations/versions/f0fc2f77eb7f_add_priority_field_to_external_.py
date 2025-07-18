"""Add priority field to external_transaction_model

Revision ID: f0fc2f77eb7f
Revises: ab3e5b2a31ee
Create Date: 2024-09-11 12:43:39.173850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f0fc2f77eb7f'
down_revision: Union[str, None] = 'ab3e5b2a31ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('external_transaction_model', sa.Column('priority', sa.BigInteger(), nullable=True))

    op.execute("""
    UPDATE external_transaction_model
    SET priority = CASE
        WHEN status IN ('pending', 'processing') THEN
            -CAST(EXTRACT(EPOCH FROM (TIMESTAMP '3000-01-01' - create_timestamp)) AS BIGINT)
        ELSE
            CAST(EXTRACT(EPOCH FROM (TIMESTAMP '3000-01-01' - create_timestamp)) AS BIGINT)
    END;
    """)

    op.alter_column('external_transaction_model', 'priority', nullable=False)


def downgrade():
    op.drop_column('external_transaction_model', 'priority')
