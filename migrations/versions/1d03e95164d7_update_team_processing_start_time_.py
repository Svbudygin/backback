"""update team processing start time trigger

Revision ID: 1d03e95164d7
Revises: 466862115d16
Create Date: 2025-06-11 15:17:38.959217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d03e95164d7'
down_revision: Union[str, None] = '466862115d16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION update_team_processing_start_time()
        RETURNS TRIGGER AS $$
        BEGIN
           IF (
               NEW.is_team_statement_required = TRUE OR
               (
                    NEW.close_timestamp IS NULL AND
                    NEW.is_merchant_statement_required = FALSE AND
                    NEW.is_support_confirmation_required = FALSE
               )
           ) THEN
               IF NEW.team_processing_start_time IS NULL THEN
                   NEW.team_processing_start_time := NOW();
               END IF;
           ELSE
               NEW.team_processing_start_time := NULL;
               NEW.timeout_expired := FALSE;
           END IF;

           RETURN NEW;
       END;
       $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION update_team_processing_start_time()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (
                NEW.is_team_statement_required = TRUE OR
                (
                    NEW.close_timestamp IS NULL AND
                    NEW.is_merchant_statement_required = FALSE
                )
            ) THEN
                IF NEW.team_processing_start_time IS NULL THEN
                    NEW.team_processing_start_time := NOW();
                END IF;
            ELSE
                NEW.team_processing_start_time := NULL;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
