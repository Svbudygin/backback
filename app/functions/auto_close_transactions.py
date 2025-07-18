import datetime

from sqlalchemy import select, text, func

from app.core.constants import (
    AUTO_CLOSE_INTERNAL_TRANSACTIONS_S,
    Status,
    Direction,
    AUTO_CLOSE_EXTERNAL_TRANSACTIONS_S)

from app.core.session import async_session
from app.enums import TransactionFinalStatusEnum
from app.models import ExternalTransactionModel
from app.functions import external_transaction as e_t_f


async def auto_close_transactions():
    async with async_session() as session:
        close_inbound_transactions_q = await session.execute(
            text(f"""
            select e.id, e.team_id
            from external_transaction_model e inner join merchants m
                                                         on e.merchant_id = m.id
            where status = '{Status.PENDING}'
            and direction = '{Direction.INBOUND}'
            and e.create_timestamp <= now() - INTERVAL '1 second' * m.transaction_auto_close_time_s;
            """)
        )
        for trx_id, team_id in close_inbound_transactions_q.all():
            await e_t_f.external_transaction_update_(
                transaction_id=trx_id,
                session=session,
                status=Status.CLOSE,
                close_if_accept=False,
                final_status=TransactionFinalStatusEnum.TIMEOUT
            )
        
        close_outbound_transactions_q = await session.execute(
            text(f"""
            select e.id, e.merchant_id
            from external_transaction_model e inner join merchants m
                                                         on e.merchant_id = m.id
            where status = '{Status.PENDING}'
            and direction = '{Direction.OUTBOUND}'
            and e.team_id is null
            and e.create_timestamp <= now() - INTERVAL '1 second' * m.transaction_outbound_auto_close_time_s;
            """)
        )
        for trx_id, m_id in close_outbound_transactions_q.all():
            await e_t_f.external_transaction_update_(
                transaction_id=trx_id,
                session=session,
                status=Status.CLOSE,
                close_if_accept=False,
                final_status=TransactionFinalStatusEnum.TIMEOUT
            )
        
        # await session.execute(text(f"""
        #     do
        #     $$
        #         DECLARE
        #             current_time_ timestamp := now();
        #         BEGIN
        #             INSERT INTO user_balance_change_model
        #                 (user_id, profit_balance, trust_balance, locked_balance)
        #                 (SELECT u.id, 0, SUM(t.amount * {DECIMALS} / t.exchange_rate),
        #                         -SUM(t.amount * {DECIMALS} / t.exchange_rate)
        #
        #                 FROM user_model u
        #                           inner join external_transaction_model t on u.id = t.team_id
        #                           inner join user_model v on v.id = t.merchant_id
        #                 AND t.status = 'pending'
        #                 AND t.direction = 'inbound'
        #                 AND t.create_timestamp < current_time_ - INTERVAL '1 second' * v.transaction_auto_close_time_s
        #                  GROUP BY u.id);
        #
        #             UPDATE external_transaction_model z
        #             SET status = 'close'
        #
        #             FROM external_transaction_model t
        #                      INNER JOIN user_model u ON t.merchant_id = u.id
        #             WHERE z.status = 'pending'
        #               AND z.direction = 'inbound'
        #               AND z.id = t.id
        #               AND z.create_timestamp < current_time_ - INTERVAL '1 second' * u.transaction_auto_close_time_s;
        #         end;
        #     $$;
        # """))
        # await session.commit()
        await session.execute(text(f"""
            UPDATE internal_transaction_model
            SET status = 'close'
            WHERE status = 'pending'
            AND direction = 'inbound'
            AND create_timestamp < NOW() - INTERVAL '{AUTO_CLOSE_INTERNAL_TRANSACTIONS_S} second';
        """))
        
        await session.commit()
