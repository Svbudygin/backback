"""added message fields

Revision ID: fcfb5e9ec158
Revises: 9c063c5dd33f
Create Date: 2024-08-03 11:43:37.611847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcfb5e9ec158'
down_revision: Union[str, None] = '9c063c5dd33f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('bank_detail_model_offset_id_index', table_name='bank_detail_model')
    op.create_index('bank_detail_model_offset_id_index', 'bank_detail_model', ['number', 'bank', 'type', 'is_deleted'], unique=False)
    op.drop_index('ix_message_model_epoch', table_name='message_model')
    op.drop_constraint('message_cache', 'message_model', type_='unique')
    op.drop_column('message_model', 'epoch')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('message_model', sa.Column('epoch', sa.BIGINT(), autoincrement=False, nullable=True))
    op.create_unique_constraint('message_cache', 'message_model', ['amount', 'comment', 'epoch', 'device_hash'])
    op.create_index('ix_message_model_epoch', 'message_model', ['epoch'], unique=False)
    op.drop_index('bank_detail_model_offset_id_index', table_name='bank_detail_model')
    op.create_index('bank_detail_model_offset_id_index', 'bank_detail_model', ['offset_id'], unique=False)
    # ### end Alembic commands ###
