"""Add is_vip and new table

Revision ID: 0309b9814811
Revises: 7c97d56366ba
Create Date: 2025-03-19 16:25:06.830898

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0309b9814811'
down_revision: Union[str, None] = '7c97d56366ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'vip_payer_model',
        sa.Column('payer_id', sa.String(length=64), nullable=False),
        sa.Column('merchant_id', sa.String(length=64), nullable=False),
        sa.Column('bank_detail_id', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['bank_detail_id'], ['bank_detail_model.id']),
        sa.PrimaryKeyConstraint('payer_id', 'merchant_id')
    )
    op.create_index('idx_vip_payer_merchant', 'vip_payer_model', ['payer_id', 'merchant_id'], unique=False)
    op.create_index('idx_vip_payer_bank', 'vip_payer_model', ['bank_detail_id'], unique=False)
    op.add_column('bank_detail_model', sa.Column('is_vip', sa.Boolean(), nullable=False, server_default="FALSE"))
    op.create_index('idx_bank_detail_vip', 'bank_detail_model', ['is_vip'], unique=False)

def downgrade() -> None:
    op.drop_index('idx_bank_detail_vip', table_name='bank_detail_model')
    op.drop_column('bank_detail_model', 'is_vip')
    op.drop_index('idx_vip_payer_merchant', table_name='vip_payer_model')
    op.drop_index('idx_vip_payer_bank', table_name='vip_payer_model')
    op.drop_table('vip_payer_model')
