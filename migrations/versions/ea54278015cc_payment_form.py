"""payment_form

Revision ID: ea54278015cc
Revises: 7e16323c30fd
Create Date: 2024-09-27 08:09:15.023815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea54278015cc'
down_revision: Union[str, None] = '7e16323c30fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('payment_forms',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('merchant_transaction_id', sa.String(length=64), nullable=False),
    sa.Column('merchant_id', sa.String(length=64), nullable=False),
    sa.Column('hook_uri', sa.String(length=1024), nullable=True),
    sa.Column('payer_id', sa.String(length=64), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('return_url', sa.String(length=1024), nullable=True),
    sa.Column('success_url', sa.String(length=1024), nullable=True),
    sa.Column('fail_url', sa.String(length=1024), nullable=True),
    sa.Column('merchant_website_name', sa.String(length=1024), nullable=True),
    sa.Column('config', sa.JSON(), nullable=False),
    sa.Column('create_timestamp', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('sberpay_link', sa.String(), nullable=True),
    sa.Column('method', sa.String(), nullable=True),
    sa.Column('currency_name', sa.String(), nullable=False),
    sa.Column('auto_close_time', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('payment_forms')
    # ### end Alembic commands ###
