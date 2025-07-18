from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.models import ExternalTransactionModel, BankDetailModel
from sqlalchemy.sql import func, and_

# revision identifiers, used by Alembic.
revision: str = '27c92dbc53a6'
down_revision: Union[str, None] = '63c9a40c7a55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('bank_detail_model', sa.Column('transactions_count_limit', sa.JSON(), nullable=True))
    op.add_column('bank_detail_model', sa.Column('pending_count', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('bank_detail_model', sa.Column('auto_managed', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    op.drop_index('bank_detail_model_offset_id_index', table_name='bank_detail_model')
    op.create_index('bank_detail_model_offset_id_index', 'bank_detail_model', ['number', 'bank', 'type', 'is_deleted'],
                    unique=False)
    op.create_index(op.f('ix_bank_detail_model_auto_managed'), 'bank_detail_model', ['auto_managed'], unique=False)


def downgrade() -> None:
    # Удаляем все изменения в случае отката
    op.drop_index(op.f('ix_bank_detail_model_auto_managed'), table_name='bank_detail_model')
    op.drop_index('bank_detail_model_offset_id_index', table_name='bank_detail_model')
    op.create_index('bank_detail_model_offset_id_index', 'bank_detail_model', ['offset_id'], unique=False)

    # Удаляем добавленные колонки
    op.drop_column('bank_detail_model', 'auto_managed')
    op.drop_column('bank_detail_model', 'pending_count')
    op.drop_column('bank_detail_model', 'transactions_count_limit')
