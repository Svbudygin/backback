"""add last_accept_timestamp to VipPayerModel

Revision ID: 660b3c1ef935
Revises: 2e919eea7823
Create Date: 2025-03-27 11:49:54.105124

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '660b3c1ef935'
down_revision: Union[str, None] = '2e919eea7823'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vip_payer_model', sa.Column('last_accept_timestamp', sa.TIMESTAMP(), nullable=True))
    op.create_index('idx_vip_payer_accept_tx', 'vip_payer_model', ['last_accept_timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_vip_payer_accept_tx', table_name='vip_payer_model')
    op.drop_column('vip_payer_model', 'last_accept_timestamp')
    # ### end Alembic commands ###
