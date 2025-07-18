"""payment_system bank_detail

Revision ID: bf6d49d33c6d
Revises: d05c3ab4dd17
Create Date: 2024-11-21 11:00:02.596412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf6d49d33c6d'
down_revision: Union[str, None] = 'd05c3ab4dd17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bank_detail_model', sa.Column('payment_system', sa.String(length=64), nullable=True))
    op.drop_index('bank_detail_model_offset_id_index', table_name='bank_detail_model')
    op.create_index('bank_detail_model_offset_id_index', 'bank_detail_model', ['offset_id'], unique=False)
    op.create_index(op.f('ix_bank_detail_model_payment_system'), 'bank_detail_model', ['payment_system'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_bank_detail_model_payment_system'), table_name='bank_detail_model')
    op.drop_index('bank_detail_model_offset_id_index', table_name='bank_detail_model')
    op.create_index('bank_detail_model_offset_id_index', 'bank_detail_model', ['number', 'bank', 'type', 'is_deleted'], unique=False)
    op.drop_column('bank_detail_model', 'payment_system')
    # ### end Alembic commands ###
