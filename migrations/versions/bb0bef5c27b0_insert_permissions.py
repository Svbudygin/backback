"""insert permissions

Revision ID: bb0bef5c27b0
Revises: 1b213cd406e3
Create Date: 2024-07-26 08:09:03.308264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb0bef5c27b0'
down_revision: Union[str, None] = '1b213cd406e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
            INSERT INTO permissions (code, name)
            VALUES
                ('VIEW_TRAFFIC', 'Can view traffic'),
                ('VIEW_FEE', 'Can view fee'),
                ('VIEW_PAY_IN', 'Can view pay in'),
                ('VIEW_PAY_OUT', 'Can view pay out'),
                ('VIEW_TEAMS', 'Can view teams'),
                ('VIEW_MERCHANTS', 'Can view merchants'),
                ('VIEW_AGENTS', 'Can view agents'),
                ('VIEW_WALLET', 'Can view wallet'),
                ('VIEW_SUPPORTS', 'Can view supports')
            ON CONFLICT (code) DO NOTHING;
        """)


def downgrade() -> None:
    op.execute("""
            DELETE FROM permissions
            WHERE code IN (
                'VIEW_TRAFFIC',
                'VIEW_FEE',
                'VIEW_PAY_IN',
                'VIEW_PAY_OUT',
                'VIEW_TEAMS',
                'VIEW_MERCHANTS',
                'VIEW_AGENTS',
                'VIEW_WALLET',
                'VIEW_SUPPORTS'
            );
        """)
