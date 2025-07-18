import asyncio

from datetime import datetime, timedelta
from sqlalchemy import select, func, text
from sqlalchemy.dialects.postgresql import INTERVAL
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import concat
from sqlalchemy.orm import aliased

from app.core.constants import Direction, DECIMALS, Status, Role
from app.core.session import async_session, ro_async_session
from app.models import StatisticsModel, ExternalTransactionModel, UserBalanceChangeModel, UserModel
from app.schemas.StatisticsScheme import StatisticsResponse, StatisticsRequest, WeekTurnoverResponse


async def _get_profit(session: AsyncSession,
                      request: StatisticsRequest):
    if request.role == Role.TEAM:
        query = f"""
                        SELECT
                            SUM(fiat_profit_balance),
                            SUM(
                                CASE
                                    WHEN direction = '{Direction.OUTBOUND}' AND status = '{Status.ACCEPT}'
                                    THEN c.locked_balance +
                                        (c.trust_balance::numeric(38, 0) -
                                        amount::numeric(38, 0) *
                                        {DECIMALS}::numeric(38, 0) / exchange_rate::numeric(38, 0))::numeric(38, 0)
                                    ELSE 0
                                END
                            )
                        FROM (
                            SELECT
                                MAX(c.create_timestamp) AS create_timestamp,
                                SUM(trust_balance) AS trust_balance,
                                SUM(locked_balance) AS locked_balance,
                                SUM(fiat_profit_balance) AS fiat_profit_balance,
                                status,
                                direction,
                                amount,
                                exchange_rate,
                                balance_id
                            FROM
                                user_balance_change_model c
                            INNER JOIN
                                external_transaction_model e
                            ON
                                c.transaction_id = e.id
                            WHERE
                                c.balance_id = '{request.balance_id}'
                                AND c.create_timestamp >= '{request.date_from}'
                                AND c.create_timestamp < '{request.date_to}'
                            GROUP BY
                                c.transaction_id, status, direction, amount, exchange_rate, balance_id
                        ) c;
                        """
        profit_balances_q = await session.execute(text(query))
    else:
        profit_balances_q = await session.execute(
            text(
                f"""
        SELECT sum(CASE when direction = '{Direction.INBOUND}'
                  then c.trust_balance + c.locked_balance + c.profit_balance else 0 end ),
               sum(CASE when direction = '{Direction.OUTBOUND}'
                  then c.trust_balance + c.locked_balance + c.profit_balance else 0 end)
        FROM user_balance_change_model c INNER JOIN
             external_transaction_model e on c.transaction_id = e.id
        WHERE balance_id = '{request.balance_id}'
          AND c.create_timestamp >= '{request.date_from}'
          AND c.create_timestamp < '{request.date_to}'
                        """
            )
        )
    profit_balances = profit_balances_q.first()
    if request.direction == Direction.OUTBOUND:
        return profit_balances[1] or 0
    else:
        return profit_balances[0] or 0


async def _get_external(session: AsyncSession,
                        balance_id: str,
                        role: str,
                        date_from: datetime,
                        date_to: datetime,
                        direction: str,
                        status: str,
                        ):
    if role == Role.AGENT:
        return 0
    subquery = f"""
        SELECT id FROM user_model WHERE balance_id = '{balance_id}'
    """
    if role == Role.MERCHANT:
        where_cond = f"e.merchant_id IN ({subquery})"
    elif role == Role.TEAM:
        where_cond = f"e.team_id IN ({subquery})"
    ext_q = await session.execute(
        text(f"""SELECT SUM(e.amount::numeric(38, 0) *
                            {DECIMALS}::numeric(38, 0) / e.exchange_rate::numeric(38, 0))::numeric(38, 0)
                    FROM external_transaction_model e
                    WHERE {where_cond}
                    AND e.final_status_timestamp >= '{date_from}'
                    AND e.final_status_timestamp < '{date_to}'
                    AND e.direction = '{direction}'
                    AND e.status = '{status}'
    """)
    )
    ext = ext_q.scalars().first()
    if ext is None:
        ext = 0
    return int(ext)


async def _get_pending(
        session: AsyncSession,
        user_id: str,
        role: str,
        direction: str,
):
    profit_q = await session.execute(
        select(
            func.count()
        ).filter(
            ExternalTransactionModel.status == Status.PENDING,
            
            ExternalTransactionModel.team_id == user_id
            if role == Role.TEAM else
            ExternalTransactionModel.merchant_id == user_id,
            
            ExternalTransactionModel.direction == direction
        )
    )
    profit = profit_q.scalars().first()
    if profit is None:
        profit = 0
    return profit


async def calculate_statistics(
        request: StatisticsRequest
) -> StatisticsResponse:
    async with ro_async_session() as session:
        profit = await _get_profit(session, request)
        accept = await _get_external(session, request.balance_id, request.role, request.date_from, request.date_to, request.direction, 'accept')
        decline = await _get_external(session, request.balance_id, request.role, request.date_from, request.date_to, request.direction, 'close')
    return StatisticsResponse(
        total_volume=accept + decline,
        profit=profit,
        accept=accept,
        decline=decline
        #pending=pending
    )


async def get_week_turnover_calc(
        id: str
) -> WeekTurnoverResponse:
    async with ro_async_session() as session:
        date_to = datetime.utcnow()
        date_from = (date_to - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        inbound_trans = aliased(ExternalTransactionModel)
        outbound_trans = aliased(ExternalTransactionModel)
        isMerchant = False
        check_query = (
            select(UserModel.role).filter(UserModel.id == id)
        )
        result = await session.execute(check_query)
        scalar_result = result.scalar()

        if scalar_result == Role.MERCHANT:
            isMerchant = True
        pay_in_query = (
            select(
                func.sum(inbound_trans.amount).label("pay_in")
            )
            .filter(
                inbound_trans.direction == "inbound",
                inbound_trans.merchant_id == id if isMerchant else inbound_trans.team_id == id,
                inbound_trans.create_timestamp.between(date_from, date_to)
            )
        )
        pay_out_query = (
            select(
                func.sum(outbound_trans.amount).label("pay_out")
            )
            .filter(
                outbound_trans.direction == "outbound",
                outbound_trans.merchant_id == id if isMerchant else outbound_trans.team_id == id,
                outbound_trans.create_timestamp.between(date_from, date_to)
            )
        )
        pay_in_result = await session.execute(pay_in_query)
        pay_in = pay_in_result.scalar() or 0

        pay_out_result = await session.execute(pay_out_query)
        pay_out = pay_out_result.scalar() or 0

        return WeekTurnoverResponse(
            date_to=date_to,
            date_from=date_from,
            pay_in=pay_in // 1000000,
            pay_out=pay_out // 1000000
        )

# if __name__ == '__main__':
#     asyncio.run(calculate_statistics(
#         user_id='d6334864-fb73-4748-8d30-4e39a18d6cb3', interval_s=6000, direction=Direction.INBOUND
#     ))
