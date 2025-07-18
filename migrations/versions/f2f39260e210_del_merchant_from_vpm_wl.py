"""del merchant from vpm, wl

Revision ID: f2f39260e210
Revises: 017a5cd13504
Create Date: 2025-06-18 17:32:24.507636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f2f39260e210'
down_revision: Union[str, None] = '017a5cd13504'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DELETE FROM vip_payer_model
        WHERE ctid NOT IN (
            SELECT MIN(ctid)
            FROM vip_payer_model
            GROUP BY payer_id, bank_detail_id
        )
    """)

    op.drop_index('idx_vip_payer_merchant', table_name='vip_payer_model')
    op.drop_constraint('uq_vip_payer_triple', 'vip_payer_model', type_='unique')

    op.create_index('idx_vip_payer', 'vip_payer_model', ['payer_id'], unique=False)
    op.create_unique_constraint('uq_vip_payer_pair', 'vip_payer_model', ['payer_id', 'bank_detail_id'])

    op.drop_column('vip_payer_model', 'merchant_id')

    op.execute("""
        DELETE FROM whitelist_payer_id_model
        WHERE (payer_id, merchant_id) NOT IN (
            SELECT payer_id, merchant_id FROM (
                SELECT payer_id, merchant_id,
                       ROW_NUMBER() OVER (PARTITION BY payer_id ORDER BY merchant_id) AS rn
                FROM whitelist_payer_id_model
            ) sub
            WHERE rn = 1
        )
    """)

    op.drop_index('idx_whitelist_payer_merchant', table_name='whitelist_payer_id_model')
    op.create_index('idx_whitelist_payer_merchant', 'whitelist_payer_id_model', ['payer_id'], unique=False)
    op.drop_column('whitelist_payer_id_model', 'merchant_id')

    op.execute("""
    CREATE OR REPLACE FUNCTION check_vip_payer_limit()
    RETURNS trigger AS $$
    DECLARE
        cnt INTEGER;
        max_allowed INTEGER := 2;
    BEGIN
        SELECT COUNT(*) INTO cnt
        FROM vip_payer_model
        WHERE payer_id = NEW.payer_id
          AND LENGTH(bank_detail_id) = LENGTH(NEW.bank_detail_id);

        IF cnt >= max_allowed THEN
            RAISE EXCEPTION 'VIP payer has reached max allowed bank_detail links (%).', max_allowed;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.add_column('vip_payer_model', sa.Column('merchant_id', sa.String(length=64), nullable=True))

    op.execute("""
        WITH numbered AS (
            SELECT ctid, ROW_NUMBER() OVER (ORDER BY payer_id) AS rn
            FROM vip_payer_model
        )
        UPDATE vip_payer_model v
        SET merchant_id = 'restored_' || n.rn
        FROM numbered n
        WHERE v.ctid = n.ctid;
    """)

    op.alter_column('vip_payer_model', 'merchant_id', nullable=False)

    op.drop_constraint('uq_vip_payer_pair', 'vip_payer_model', type_='unique')
    op.drop_index('idx_vip_payer', table_name='vip_payer_model')

    op.create_index('idx_vip_payer_merchant', 'vip_payer_model', ['payer_id', 'merchant_id'], unique=False)
    op.create_unique_constraint('uq_vip_payer_triple', 'vip_payer_model', ['payer_id', 'merchant_id', 'bank_detail_id'])


    op.add_column('whitelist_payer_id_model', sa.Column('merchant_id', sa.String(length=64), nullable=True))

    op.execute("""
        WITH numbered AS (
            SELECT ctid, ROW_NUMBER() OVER (ORDER BY payer_id) AS rn
            FROM whitelist_payer_id_model
        )
        UPDATE whitelist_payer_id_model w
        SET merchant_id = 'restored_' || n.rn
        FROM numbered n
        WHERE w.ctid = n.ctid;
    """)

    op.alter_column('whitelist_payer_id_model', 'merchant_id', nullable=False)
    op.drop_index('idx_whitelist_payer_merchant', table_name='whitelist_payer_id_model')
    op.create_index('idx_whitelist_payer_merchant', 'whitelist_payer_id_model', ['payer_id', 'merchant_id'], unique=False)

    op.execute("""
    CREATE OR REPLACE FUNCTION check_vip_payer_limit()
    RETURNS trigger AS $$
    DECLARE
        cnt INTEGER;
        max_allowed INTEGER := 2;
    BEGIN
        SELECT COUNT(*) INTO cnt
        FROM vip_payer_model
        WHERE payer_id = NEW.payer_id AND merchant_id = NEW.merchant_id;
          AND LENGTH(bank_detail_id) = LENGTH(NEW.bank_detail_id);

        IF cnt >= max_allowed THEN
            RAISE EXCEPTION 'VIP payer has reached max allowed bank_detail links (%).', max_allowed;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
