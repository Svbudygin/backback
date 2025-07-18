"""tags

Revision ID: 240574d3b8f2
Revises: 
Create Date: 2024-07-02 13:27:50.549717

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '240574d3b8f2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    tag_table = op.create_table('tag_model',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('code', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('create_timestamp', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('name')
    )

    default_tag_id = str(uuid.uuid4())
    op.bulk_insert(
        tag_table,
        [
            {
                'id': default_tag_id,
                'code': "default",
                'name': "default",
            }
        ]
    )

    op.add_column('external_transaction_model', sa.Column('tag_id', sa.String(length=64), nullable=False, server_default=default_tag_id))
    op.add_column('fee_contract_model', sa.Column('tag_id', sa.String(length=64), nullable=False, server_default=default_tag_id))

    op.execute("UPDATE external_transaction_model SET tag_id = '{}' WHERE tag_id IS NULL".format(default_tag_id))
    op.execute("UPDATE fee_contract_model SET tag_id = '{}' WHERE tag_id IS NULL".format(default_tag_id))

    op.create_foreign_key(None, 'external_transaction_model', 'tag_model', ['tag_id'], ['id'])
    op.create_foreign_key(None, 'fee_contract_model', 'tag_model', ['tag_id'], ['id'])

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'fee_contract_model', type_='foreignkey')
    op.drop_column('fee_contract_model', 'tag_id')
    op.drop_constraint(None, 'external_transaction_model', type_='foreignkey')
    op.drop_column('external_transaction_model', 'tag_id')
    op.drop_table('tag_model')
    # ### end Alembic commands ###
