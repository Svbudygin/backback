"""upd or_eq

Revision ID: ea08f9fa6fd7
Revises: a97a0ff2f369
Create Date: 2025-05-20 12:13:50.978323

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea08f9fa6fd7'
down_revision: Union[str, None] = 'a97a0ff2f369'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('traffic_weight_contact_model', 'outbound_amount_less',
                    new_column_name='outbound_amount_less_or_eq')
    op.alter_column('traffic_weight_contact_model', 'outbound_amount_great',
                    new_column_name='outbound_amount_great_or_eq')


def downgrade() -> None:
    op.alter_column('traffic_weight_contact_model', 'outbound_amount_less_or_eq',
                    new_column_name='outbound_amount_less')
    op.alter_column('traffic_weight_contact_model', 'outbound_amount_great_or_eq',
                    new_column_name='outbound_amount_great')

