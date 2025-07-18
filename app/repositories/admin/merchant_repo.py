from typing import List
import asyncio
from sqlalchemy import func, select, true, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.constants import Status
from app.models import (
    ExternalTransactionModel,
    UserBalanceChangeNonceModel,
    UserModel,
    MerchantModel, CurrencyModel
)
from app.schemas.admin.MerchantScheme import MerchantResponseScheme, V2MerchantResponseScheme
from app.utils.session import get_session
from app.functions.balance import get_balances_for_multiple_ids


class MerchantRepo:
    @classmethod
    async def get(
            cls, session: AsyncSession, merch_id: str
    ) -> V2MerchantResponseScheme | None:
        async with get_session(session) as session:
            query = (
                select(MerchantModel)
                .filter(merch_id == MerchantModel.id)
            )

            result = await session.execute(query)
            user_row = result.scalar_one_or_none()

            if not user_row:
                return None

            balance_data = await get_balances_for_multiple_ids(session, [user_row.balance_id])

            balance_values = balance_data.get(user_row.balance_id, [0, 0, 0, 0, 0, 0])

            pay_in, pay_out = (
                await cls._calculate_per_ext_trans(session, merch_id)
            )

            data = {
                **{k: v for k, v in user_row.__dict__.items() if k != "api_secret"},
                "trust_balance": balance_values[0],
                "locked_balance": balance_values[1],
                "profit_balance": balance_values[2],
                "fiat_trust_balance": balance_values[3],
                "fiat_locked_balance": balance_values[4],
                "fiat_profit_balance": balance_values[5],
                "pay_in": pay_in,
                "pay_out": pay_out,
            }

            return V2MerchantResponseScheme.model_validate(data)

    @classmethod
    async def list(
        cls, *, session: AsyncSession, geo_id: int | None, namespace_id: int
    ) -> List[V2MerchantResponseScheme]:
        async with get_session(session) as session:
            query = (
                select(MerchantModel)
                .filter(
                    MerchantModel.namespace_id == namespace_id,
                    true() if geo_id is None else MerchantModel.geo_id == geo_id,
                )
                .order_by(
                    MerchantModel.is_blocked,
                    case((MerchantModel.is_inbound_enabled == True, 1), else_=0).desc(),
                    case((MerchantModel.is_outbound_enabled == True, 1), else_=0).desc(),
                    MerchantModel.name
                )
            )

            result = await session.execute(query)
            user_rows = result.scalars().all()

            if not user_rows:
                return []

            balance_ids = [row.balance_id for row in user_rows]
            balances = await get_balances_for_multiple_ids(session, balance_ids)
            merchant_ids = [row.id for row in user_rows]

            transaction_query = (
                select(
                    ExternalTransactionModel.merchant_id,
                    func.count().filter(
                        ExternalTransactionModel.direction == "inbound",
                        ExternalTransactionModel.status == Status.PENDING
                    ).label("pay_in"),
                    func.count().filter(
                        ExternalTransactionModel.direction == "outbound",
                        ExternalTransactionModel.status == Status.PENDING
                    ).label("pay_out")
                )
                .filter(ExternalTransactionModel.merchant_id.in_(merchant_ids))
                .group_by(ExternalTransactionModel.merchant_id)
            )

            transaction_result = await session.execute(transaction_query)
            transaction_rows = transaction_result.fetchall()

            transaction_data = {
                row.merchant_id: {"pay_in": row.pay_in, "pay_out": row.pay_out}
                for row in transaction_rows
            }

            results = []
            for row in user_rows:
                merchant_data = {k: v for k, v in row.__dict__.items() if k != "api_secret"}
                merchant_id = row.id

                balance_values = balances.get(row.balance_id, [0, 0, 0, 0, 0, 0])
                balance_data = {
                    "balance_id": row.balance_id,
                    "trust_balance": balance_values[0],
                    "locked_balance": balance_values[1],
                    "profit_balance": balance_values[2],
                    "fiat_trust_balance": balance_values[3],
                    "fiat_locked_balance": balance_values[4],
                    "fiat_profit_balance": balance_values[5],
                }
                pay_in = transaction_data.get(merchant_id, {}).get("pay_in", 0)
                pay_out = transaction_data.get(merchant_id, {}).get("pay_out", 0)
                data = {
                    **balance_data,
                    **merchant_data,
                    "pay_in": pay_in,
                    "pay_out": pay_out,
                }

                results.append(V2MerchantResponseScheme.model_validate(data))

            return results

    @classmethod
    async def _calculate_per_ext_trans(cls, session: AsyncSession, merch_id: str):
        """
        Aggregates data per external transaction
        """
        inbound_trans = aliased(ExternalTransactionModel)
        outbound_trans = aliased(ExternalTransactionModel)

        # Pay in ExternalTransactionModel
        pay_in_query_1 = (
            select(
                func.count(inbound_trans.id)
                .filter(
                    inbound_trans.direction == "inbound",
                    inbound_trans.status == Status.PENDING,
                    inbound_trans.merchant_id == merch_id,
                )
                .label("pay_in_1")
            )
            .select_from(UserModel)
            .outerjoin(
                inbound_trans,
                inbound_trans.merchant_id == UserModel.id,
            )
            .where(UserModel.id == merch_id)
        )

        # Pay out ExternalTransactionModel
        pay_out_query_1 = (
            select(
                func.count(outbound_trans.id)
                .filter(
                    outbound_trans.direction == "outbound",
                    outbound_trans.status == Status.PENDING,
                    outbound_trans.merchant_id == merch_id,
                )
                .label("pay_out_1")
            )
            .select_from(UserModel)
            .outerjoin(
                outbound_trans,
                outbound_trans.merchant_id == UserModel.id,
            )
            .where(UserModel.id == merch_id)
        )

        results = await asyncio.gather(
            session.execute(pay_in_query_1),
            session.execute(pay_out_query_1),
        )

        (
            pay_in_result_1,
            pay_out_result_1,
        ) = results

        pay_in_1 = pay_in_result_1.scalar() or 0
        pay_out_1 = pay_out_result_1.scalar() or 0

        pay_in = pay_in_1
        pay_out = pay_out_1

        return pay_in, pay_out

    @classmethod
    async def update(cls, *, session: AsyncSession = None, user_id: str, **kwargs):
        async with get_session(session) as session:
            merch = (await session.execute(
                select(MerchantModel)
                .where(MerchantModel.id == user_id)
            )).scalar_one_or_none()

            if merch is None:
                return None

            old_currency_id = merch.currency_id
            for key, value in kwargs.items():
                if hasattr(merch, key):
                    setattr(merch, key, value)
            if 'currency_id' in kwargs:
                new_currency_id = kwargs['currency_id']
                new_currency = await session.execute(
                    select(CurrencyModel)
                    .where(CurrencyModel.id == new_currency_id)
                )
                new_currency = new_currency.scalar_one_or_none()
                merch.currency = new_currency

            await session.commit()
            return await cls.get(session=session, merch_id=user_id)
