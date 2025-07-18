"""init models

Revision ID: 65ce354f5f5b
Revises: 02f48b1b65b1
Create Date: 2024-09-12 22:45:11.178959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65ce354f5f5b'
down_revision: Union[str, None] = '02f48b1b65b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('bank_detail_model_offset_id_index', table_name='bank_detail_model')
    op.create_index('bank_detail_model_offset_id_index', 'bank_detail_model', ['number', 'bank', 'type', 'is_deleted'], unique=False)
    op.create_index(op.f('ix_external_transaction_model_status'), 'external_transaction_model', ['status'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_external_transaction_model_status'), table_name='external_transaction_model')
    op.drop_index('bank_detail_model_offset_id_index', table_name='bank_detail_model')
    op.create_index('bank_detail_model_offset_id_index', 'bank_detail_model', ['offset_id'], unique=False)
    # ### end Alembic commands ###
