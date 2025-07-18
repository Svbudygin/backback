"""upd TeamModel, add TransferAssociationModel

Revision ID: 86014223b5f0
Revises: ac9830a2eaac
Create Date: 2025-04-14 11:54:47.346720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86014223b5f0'
down_revision: Union[str, None] = 'ac9830a2eaac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'transfer_association_model',
        sa.Column('team_id', sa.String(length=64), nullable=False),
        sa.Column('transaction_id', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('team_id', 'transaction_id')
    )
    op.create_index(
        'idx_transfer_association_team_id',
        'transfer_association_model',
        ['team_id'],
        unique=False
    )

    op.add_column('teams', sa.Column(
        'fiat_max_outbound',
        sa.BigInteger(),
        nullable=False,
        server_default=str((2 ** 32) - 1)
    ))
    op.add_column('teams', sa.Column(
        'fiat_min_outbound',
        sa.BigInteger(),
        nullable=False,
        server_default='0'
    ))
    op.add_column('teams', sa.Column(
        'today_outbound_amount_used',
        sa.BigInteger(),
        nullable=False,
        server_default='0'
    ))
    op.add_column('teams', sa.Column(
        'max_today_outbound_amount_used',
        sa.BigInteger(),
        nullable=False,
        server_default=str((2 ** 32) - 1)
    ))


def downgrade() -> None:
    op.drop_column('teams', 'max_today_outbound_amount_used')
    op.drop_column('teams', 'today_outbound_amount_used')
    op.drop_column('teams', 'fiat_min_outbound')
    op.drop_column('teams', 'fiat_max_outbound')

    op.drop_index('idx_transfer_association_team_id', table_name='transfer_association_model')
    op.drop_table('transfer_association_model')
