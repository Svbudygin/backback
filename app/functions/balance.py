import asyncio
from datetime import datetime
from typing import Tuple

from sqlalchemy import func, insert, select, text, update, table, column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, with_polymorphic
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.postgresql import dialect

from app import exceptions
from app.core.constants import DECIMALS, Direction, Role, Status
from app.core.session import async_session, ro_async_session
from app.models import CurrencyModel, UserBalanceChangeNonceModel, UserModel
from app.models.UserBalanceChangeModel import UserBalanceChangeModel
from app.schemas.BalanceScheme import (
    BalanceStatsResponse,
    UpdateCurrencyRequest,
    UpdateCurrencyResponse,
)
import logging

logger = logging.getLogger(__name__)


async def get_balance_id_by_user_id(user_id: str, session: AsyncSession):
    balance_id_q = await session.execute(
        select(UserModel.balance_id).filter(UserModel.id == user_id)
    )
    balance: str | None = balance_id_q.scalars().first()
    if balance is None:
        raise exceptions.BalanceNotFoundException()
    return balance


async def add_balance_changes(session: AsyncSession, changes: list[dict[str, int]]):
    # user_ids = list({c["user_id"] for c in changes if "user_id" in c})
    # user_model_table = table(
    #     "user_model",
    #     column("id")
    # )
    #
    # stmt = (
    #     select(user_model_table.c.id)
    #     .where(user_model_table.c.id.in_(user_ids))
    # )
    #
    # await session.execute(stmt)
    #
    # return await session.execute(
    #     insert(UserBalanceChangeModel)
    #     .values(changes)
    #     .returning(UserBalanceChangeModel)
    # )

    await session.execute(
        insert(UserBalanceChangeModel).values(changes)
    )

    values = [
        {
            "balance_id": change["balance_id"],
            "trust_balance": change.get("trust_balance", 0),
            "locked_balance": change.get("locked_balance", 0),
            "profit_balance": change.get("profit_balance", 0),
            "fiat_trust_balance": change.get("fiat_trust_balance", 0),
            "fiat_locked_balance": change.get("fiat_locked_balance", 0),
            "fiat_profit_balance": change.get("fiat_profit_balance", 0),
        }
        for change in changes
    ]

    stmt = pg_insert(UserBalanceChangeNonceModel).values(values)
    update_stmt = {
        "trust_balance": UserBalanceChangeNonceModel.trust_balance + stmt.excluded.trust_balance,
        "locked_balance": UserBalanceChangeNonceModel.locked_balance + stmt.excluded.locked_balance,
        "profit_balance": UserBalanceChangeNonceModel.profit_balance + stmt.excluded.profit_balance,
        "fiat_trust_balance": UserBalanceChangeNonceModel.fiat_trust_balance + stmt.excluded.fiat_trust_balance,
        "fiat_locked_balance": UserBalanceChangeNonceModel.fiat_locked_balance + stmt.excluded.fiat_locked_balance,
        "fiat_profit_balance": UserBalanceChangeNonceModel.fiat_profit_balance + stmt.excluded.fiat_profit_balance,
        "change_id": func.txid_current(),
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=[UserBalanceChangeNonceModel.balance_id],
        set_=update_stmt,
    )

    await session.execute(stmt)

async def get_balances_for_multiple_ids(session: AsyncSession, balance_ids: list[str]):
    # nonce_q = await session.execute(
    #     select(
    #         UserBalanceChangeNonceModel.balance_id,
    #         UserBalanceChangeNonceModel.trust_balance,
    #         UserBalanceChangeNonceModel.locked_balance,
    #         UserBalanceChangeNonceModel.profit_balance,
    #         UserBalanceChangeNonceModel.fiat_trust_balance,
    #         UserBalanceChangeNonceModel.fiat_locked_balance,
    #         UserBalanceChangeNonceModel.fiat_profit_balance,
    #     ).filter(UserBalanceChangeNonceModel.balance_id.in_(balance_ids))
    # )
    #
    # nonce_results = {
    #     row.balance_id: (
    #         row.trust_balance,
    #         row.locked_balance,
    #         row.profit_balance,
    #         row.fiat_trust_balance,
    #         row.fiat_locked_balance,
    #         row.fiat_profit_balance
    #     ) for row in nonce_q.fetchall()
    # }
    #
    # balances = {balance_id: [0, 0, 0, 0, 0, 0] for balance_id in balance_ids}
    #
    # for balance_id, values in nonce_results.items():
    #     balances[balance_id] = list(values)
    #
    # stmt = (
    #    select(
    #        UserBalanceChangeModel.balance_id,
    #        func.sum(UserBalanceChangeModel.trust_balance),
    #        func.sum(UserBalanceChangeModel.locked_balance),
    #        func.sum(UserBalanceChangeModel.profit_balance),
    #        func.sum(UserBalanceChangeModel.fiat_trust_balance),
    #        func.sum(UserBalanceChangeModel.fiat_locked_balance),
    #        func.sum(UserBalanceChangeModel.fiat_profit_balance),
    #    ).filter(
    #        UserBalanceChangeModel.balance_id.in_(balance_ids),
    #        UserBalanceChangeModel.id > func.coalesce(
    #            select(UserBalanceChangeNonceModel.change_id)
    #            .where(UserBalanceChangeNonceModel.balance_id == UserBalanceChangeModel.balance_id)
    #            .scalar_subquery(), -2
    #        ),
    #        UserBalanceChangeModel.id
    #        < func.txid_snapshot_xmin(func.txid_current_snapshot()),
    #    ).group_by(UserBalanceChangeModel.balance_id)
    # )
    #
    # compiled_query = stmt.compile(dialect=dialect(), compile_kwargs={"literal_binds": True})
    # logger.info(f"[AGGREGATED_QUERY SQL]: {compiled_query}")
    #
    # aggregated_query = await session.execute(stmt)
    #
    # for row in aggregated_query.fetchall():
    #    balance_id, trust, locked, profit, fiat_trust, fiat_locked, fiat_profit = row
    #    if balance_id in balances:
    #        balances[balance_id][0] += int(trust or 0)
    #        balances[balance_id][1] += int(locked or 0)
    #        balances[balance_id][2] += int(profit or 0)
    #        balances[balance_id][3] += int(fiat_trust or 0)
    #        balances[balance_id][4] += int(fiat_locked or 0)
    #        balances[balance_id][5] += int(fiat_profit or 0)
    #
    # return balances

    nonce_q = await session.execute(
        select(
            UserBalanceChangeNonceModel.balance_id,
            UserBalanceChangeNonceModel.trust_balance,
            UserBalanceChangeNonceModel.locked_balance,
            UserBalanceChangeNonceModel.profit_balance,
            UserBalanceChangeNonceModel.fiat_trust_balance,
            UserBalanceChangeNonceModel.fiat_locked_balance,
            UserBalanceChangeNonceModel.fiat_profit_balance,
        ).filter(UserBalanceChangeNonceModel.balance_id.in_(balance_ids))
    )

    nonce_results = {
        row.balance_id: [
            row.trust_balance,
            row.locked_balance,
            row.profit_balance,
            row.fiat_trust_balance,
            row.fiat_locked_balance,
            row.fiat_profit_balance
        ] for row in nonce_q.fetchall()
    }

    balances = {balance_id: [0, 0, 0, 0, 0, 0] for balance_id in balance_ids}

    for balance_id, values in nonce_results.items():
        balances[balance_id] = values

    return balances



async def get_balances(
        user_id: str,
        session: AsyncSession,
        is_update: bool = True,
        balance_id: str | None = None,
        is_agent: bool = True,
) -> Tuple[int, int, int, int, int, int]:
    """:returns: trust_balance, locked_balance, profit_balance"""
    #if is_agent:
    #    stmt = select(UserModel).filter(UserModel.id == user_id)
    #    result = await session.execute(stmt)
    #    user = result.scalar_one_or_none()
    #    if user is None:
    #        logger.info(f"[GetBalanceNotFoundException] - user_id = {user_id}")
    #        raise exceptions.UserNotFoundException()
    #    if user.role == Role.AGENT:
    #        is_update = True
    if balance_id is None:
        balance_id = await get_balance_id_by_user_id(user_id, session)
    nonce_q = await session.execute(
        select(
            UserBalanceChangeNonceModel.change_id,
            UserBalanceChangeNonceModel.trust_balance,
            UserBalanceChangeNonceModel.locked_balance,
            UserBalanceChangeNonceModel.profit_balance,
            UserBalanceChangeNonceModel.fiat_trust_balance,
            UserBalanceChangeNonceModel.fiat_locked_balance,
            UserBalanceChangeNonceModel.fiat_profit_balance,
        ).filter(balance_id == UserBalanceChangeNonceModel.balance_id)
    )
    nonce = nonce_q.first()
    if nonce is None:
        (
            offset,
            trust_pre_calc,
            locked_pre_calc,
            profit_pre_calc,
            fiat_trust_pre_calc,
            fiat_locked_pre_calc,
            fiat_profit_pre_calc,
        ) = (-2, 0, 0, 0, 0, 0, 0)
    else:
        (
            offset,
            trust_pre_calc,
            locked_pre_calc,
            profit_pre_calc,
            fiat_trust_pre_calc,
            fiat_locked_pre_calc,
            fiat_profit_pre_calc,
        ) = nonce
    # aggregated_query = await session.execute(
    #    select(
    #        func.sum(UserBalanceChangeModel.trust_balance),
    #        func.sum(UserBalanceChangeModel.locked_balance),
    #        func.sum(UserBalanceChangeModel.profit_balance),
    #        func.sum(UserBalanceChangeModel.fiat_trust_balance),
    #        func.sum(UserBalanceChangeModel.fiat_locked_balance),
    #        func.sum(UserBalanceChangeModel.fiat_profit_balance),
    #        func.max(UserBalanceChangeModel.id),
    #    ).filter(
    #        UserBalanceChangeModel.balance_id == balance_id,
    #        UserBalanceChangeModel.id > offset,
    #        UserBalanceChangeModel.id
    #        < func.txid_snapshot_xmin(func.txid_current_snapshot()),
    #    )
    # )
    #aggregated = aggregated_query.first()
    #offset_pre_calc = offset
    #if aggregated[0] is not None:
    #    (
    #        trust_balance,
    #        locked_balance,
    #        profit_balance,
    #        fiat_trust_balance,
    #        fiat_locked_balance,
    #        fiat_profit_balance,
    #        offset_pre_calc,
    #    ) = aggregated
    #    trust_pre_calc += int(trust_balance)
    #    locked_pre_calc += int(locked_balance)
    #    profit_pre_calc += int(profit_balance)
    #    fiat_trust_pre_calc += int(fiat_trust_balance)
    #    fiat_locked_pre_calc += int(fiat_locked_balance)
    #    fiat_profit_pre_calc += int(fiat_profit_balance)
    #if is_update and aggregated[0] is not None:
    #    changes: dict = {
    #        UserBalanceChangeNonceModel.trust_balance: trust_pre_calc,
    #        UserBalanceChangeNonceModel.locked_balance: locked_pre_calc,
    #        UserBalanceChangeNonceModel.profit_balance: profit_pre_calc,
    #        UserBalanceChangeNonceModel.fiat_trust_balance: fiat_trust_pre_calc,
    #        UserBalanceChangeNonceModel.fiat_locked_balance: fiat_locked_pre_calc,
    #        UserBalanceChangeNonceModel.fiat_profit_balance: fiat_profit_pre_calc,
    #        UserBalanceChangeNonceModel.change_id: offset_pre_calc,
    #    }
    #
    #    await session.execute(
    #        pg_insert(UserBalanceChangeNonceModel)
    #        .values({**changes, UserBalanceChangeNonceModel.balance_id: balance_id})
    #        .on_conflict_do_update(
    #            index_elements=[UserBalanceChangeNonceModel.balance_id],
    #            set_=changes,
    #        )
    #    )
    
    return (
        trust_pre_calc,
        locked_pre_calc,
        profit_pre_calc,
        fiat_trust_pre_calc,
        fiat_locked_pre_calc,
        fiat_profit_pre_calc,
    )


async def _get_currency(currency_id: str, session: AsyncSession) -> CurrencyModel:
    contract_req = await session.execute(
        select(CurrencyModel).filter(
            CurrencyModel.id == currency_id,
        )
    )
    return contract_req.scalars().first()


async def update_currency(request: UpdateCurrencyRequest):
    async with async_session() as session:
        currency_q = await session.execute(
            select(CurrencyModel).filter(
                CurrencyModel.id == request.id,
            )
        )
        currency = currency_q.scalars().first()
        if currency is None:
            raise exceptions.CurrencyNotFoundException()
        currency.update_timestamp = func.now()
        currency.inbound_exchange_rate = request.inbound_exchange_rate
        currency.outbound_exchange_rate = request.outbound_exchange_rate
        await session.commit()
        
        return UpdateCurrencyResponse(**currency.__dict__)


async def get_balances_transaction(
        user_id: str, is_update: bool = True, currency_id: str | None = None
) -> Tuple[int, int, int, int, int, int]:
    async with async_session() as session:
        balances = await get_balances(
            user_id=user_id, session=session, is_update=is_update
        )
        await session.commit()
        if currency_id is not None:
            currency: CurrencyModel = await _get_currency(
                currency_id=currency_id, session=session
            )
            
            if not currency:
                raise exceptions.CurrencyNotFoundException()
            return (
                balances[0] * currency.exchange_rate // DECIMALS,
                balances[1] * currency.exchange_rate // DECIMALS,
                balances[2] * currency.exchange_rate // DECIMALS,
                balances[3] * currency.exchange_rate // DECIMALS,
                balances[4] * currency.exchange_rate // DECIMALS,
                balances[5] * currency.exchange_rate // DECIMALS,
            )
        return (
            balances[0],
            balances[1],
            balances[2],
            balances[3],
            balances[4],
            balances[5],
        )


async def get_estimated_fiat_balance(
        user_id: str,
        currency_id: str
) -> int:
    async with ro_async_session() as session:
        balances = await get_balances(
            user_id=user_id, session=session, is_update=False
        )
        await session.commit()
        currency: CurrencyModel = await _get_currency(
            currency_id=currency_id, session=session
        )
        
        if not currency:
            raise exceptions.CurrencyNotFoundException()
        return balances[0] * currency.inbound_exchange_rate // DECIMALS


async def get_balance_stats(
        user_id: str,
        balance_id: str,
        role: str,
        date_from: datetime,
        date_to: datetime,
        is_update=False,
        is_agent=False,
) -> BalanceStatsResponse:
    session_factory = async_session if is_agent else ro_async_session
    async with session_factory() as session:
        balances = await get_balances(
            user_id=user_id, session=session, is_update=is_update, balance_id=balance_id, is_agent=is_agent
        )
        await session.commit()
        
        if role == Role.TEAM:
            query = f"""
                SELECT
                    SUM(fiat_profit_balance),
                    SUM(
                        CASE
                            WHEN direction = '{Direction.OUTBOUND}' AND status = '{Status.ACCEPT}' AND c.trust_balance > 0
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
                        c.balance_id = '{balance_id}'
                        AND c.create_timestamp >= '{date_from}'
                        AND c.create_timestamp < '{date_to}'
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
WHERE balance_id = '{balance_id}'
  AND c.create_timestamp >= '{date_from}'
  AND c.create_timestamp < '{date_to}'
                """
                )
            )
        profit_balances = profit_balances_q.first()

        return BalanceStatsResponse(
            trust_balance=balances[0] or 0,
            locked_balance=balances[1] or 0,
            fiat_trust_balance=balances[3] or 0,
            fiat_locked_balance=balances[4] or 0,
            inbound_fiat_profit_balance=profit_balances[0] or 0,
            outbound_profit_balance=profit_balances[1] or 0,
        )

# if __name__ == '__main__':
#     t = datetime.utcnow()
#     print(t.replace(minute=0, second=0, microsecond=0))
#     print(asyncio.run(get_balance_stats(
#         user_id='1e6de028-b70c-40d4-9d3f-37ee9f763a3a',
#         role='team',
#         date_from=t.replace(minute=0, second=0, microsecond=0),
#         date_to=datetime.now()
#     )))
#
# async def test():
#     async with async_session() as session:
#         uid = 'd6334864-fb73-4748-8d30-4e39a18d6cb3'
#         await add_balance_changes(
#             session,
#             [{
#                 'user_id': uid,
#                 'trust_balance': 100000000,
#             }
#             ]
#         )
#         res = await get_balances(user_id=uid, session=session)
#         await session.commit()
#         print(res)
#
#
# async def perfomance_test():
#     await asyncio.gather(*[test() for _ in range(1)])
#
# if __name__ == '__main__':
#     timer = datetime.datetime.now()
#     asyncio.run(perfomance_test())
#     print(datetime.datetime.now() - timer)
#
#async def balance_test():
#    async with ro_async_session() as session:
#       print(await get_balances(user_id="ca9d54e4-1882-4789-8dc7-dd2c897b2ada", session=session))
#
#if __name__ == '__main__':
#    asyncio.run(balance_test())
