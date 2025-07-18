"""Make merchant_transaction_id unique in external_transaction_model

Revision ID: 7e16323c30fd
Revises: 65ce354f5f5b
Create Date: 2024-09-15 18:10:42.366082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7e16323c30fd'
down_revision: Union[str, None] = '65ce354f5f5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()

    duplicates = conn.execute(
        sa.text("""
            SELECT merchant_transaction_id
            FROM external_transaction_model
            WHERE merchant_transaction_id IS NOT NULL
            GROUP BY merchant_transaction_id
            HAVING COUNT(*) > 1
        """)
    ).fetchall()

    for (merchant_transaction_id,) in duplicates:
        rows = conn.execute(
            sa.text("""
                SELECT id
                FROM external_transaction_model
                WHERE merchant_transaction_id = :merchant_transaction_id
                ORDER BY id
            """),
            {"merchant_transaction_id": merchant_transaction_id}
        ).fetchall()

        for idx, (row_id,) in enumerate(rows[1:], start=1):
            conn.execute(
                sa.text("""
                    UPDATE external_transaction_model
                    SET merchant_transaction_id = :new_id
                    WHERE id = :row_id
                """),
                {
                    "new_id": f"{merchant_transaction_id}_{idx}unique",
                    "row_id": row_id
                }
            )

    op.create_unique_constraint(
        'uq_merchant_transaction_id',
        'external_transaction_model',
        ['merchant_transaction_id']
    )


def downgrade():
    op.drop_constraint('uq_merchant_transaction_id', 'external_transaction_model', type_='unique')
