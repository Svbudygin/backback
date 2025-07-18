"""add type to TWC

Revision ID: 48faf167e2c8
Revises: 0f1fab6298ee
Create Date: 2025-04-18 10:53:40.447261
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Boolean, BigInteger, TIMESTAMP
import uuid

# revision identifiers, used by Alembic.
revision: str = '48faf167e2c8'
down_revision: Union[str, None] = '0f1fab6298ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('traffic_weight_contact_model', sa.Column('type', sa.String(length=64), nullable=False, server_default='card'))
    op.create_index(op.f('ix_traffic_weight_contact_model_type'), 'traffic_weight_contact_model', ['type'], unique=False)

    conn = op.get_bind()

    traffic_table = table(
        'traffic_weight_contact_model',
        column('id', sa.String),
        column('create_timestamp', TIMESTAMP),
        column('is_deleted', Boolean),
        column('merchant_id', sa.String),
        column('team_id', sa.String),
        column('currency_id', sa.String),
        column('type', sa.String),
        column('comment', sa.String),
        column('inbound_traffic_weight', BigInteger),
        column('outbound_traffic_weight', BigInteger),
    )

    rows = conn.execute(sa.select(traffic_table)).fetchall()

    for row in rows:
        new_id = str(uuid.uuid4())
        conn.execute(
            traffic_table.insert().values(
                id=new_id,
                create_timestamp=row.create_timestamp,
                is_deleted=row.is_deleted,
                merchant_id=row.merchant_id,
                team_id=row.team_id,
                currency_id=row.currency_id,
                type='phone',
                comment=row.comment,
                inbound_traffic_weight=row.inbound_traffic_weight,
                outbound_traffic_weight=row.outbound_traffic_weight,
            )
        )

    op.alter_column('traffic_weight_contact_model', 'type', server_default=None)


def downgrade() -> None:
    op.drop_index(op.f('ix_traffic_weight_contact_model_type'), table_name='traffic_weight_contact_model')
    op.drop_column('traffic_weight_contact_model', 'type')
