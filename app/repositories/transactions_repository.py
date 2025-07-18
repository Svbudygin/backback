from datetime import datetime, timedelta
from typing import List

from sqlalchemy import Numeric, case, cast, func, select, true
from sqlalchemy.orm import aliased

from app.core.constants import ONE_MILLION, Role
from app.core.session import async_session, ro_async_session
from app.models import ExternalTransactionModel, UserBalanceChangeModel, MessageModel, InternalTransactionModel, UserModel
from app.schemas.ExternalTransactionScheme import (
    ExportSumTransactionsResponse,
    ExportTransactionsRequest,
    ExportTransactionsResponse,
)
from app.schemas.InternalTransactionScheme import (
    ExportInternalTransactionsResponse,
    ExportInternalTransactionsRequest,
)
from app.utils.measure import measure_exe_time


def get_create_timestamp_from(timestamp):
    if timestamp is None:
        return datetime.utcnow().replace(
            hour=23, minute=59, second=59, microsecond=0
        ) - timedelta(
            days=31 * 6
        )  # 6 месяцев
    return datetime.utcfromtimestamp(timestamp)


def get_create_timestamp_to(timestamp):
    if timestamp is None:
        return datetime(2030, 1, 1)
    return datetime.utcfromtimestamp(timestamp)


class TransactionsRepository:
    @measure_exe_time
    @staticmethod
    async def filter_external_transactions_for_export(
            request: ExportTransactionsRequest,
    ) -> List[ExportTransactionsResponse]:
        async with ro_async_session() as session:
            u = aliased(UserBalanceChangeModel)
            e = aliased(ExternalTransactionModel)
            
            # Берем дату 31 день назад от текущей даты, включая сегодняший день
            date_31_days_ago = datetime.utcnow().replace(
                hour=23, minute=59, second=59, microsecond=0
            ) - timedelta(days=31)

            query = (
                select(
                    e.id.label("transaction_id"),
                    e.merchant_transaction_id,
                    e.create_timestamp,
                    e.direction,
                    e.bank_detail_number,
                    (e.amount / ONE_MILLION).label("transaction_amount"),
                    e.status,
                    (func.sum(u.trust_balance) / ONE_MILLION).label(
                        "usdt_deposit_change"
                    ),
                    (1.0 * e.exchange_rate / ONE_MILLION).label("exchange_rate"),
                    case(
                        (e.amount == 0, 0),
                        (e.exchange_rate == 0, 0),
                        (e.status == 'close', None),
                        else_=func.round(
                            cast(
                                100 * func.abs(func.abs(
                                    func.sum(u.trust_balance) /
                                    (e.amount / e.exchange_rate)
                                    / ONE_MILLION)
                                               - 1 * (request.role in [Role.TEAM, Role.MERCHANT]))
                                ,
                                Numeric
                            ),
                            2
                        )
                    ).label("interest")
                )
                .join(u, e.id == u.transaction_id, isouter=True)
                .group_by(
                    e.id,
                    e.merchant_transaction_id,
                    e.create_timestamp,
                    e.direction,
                    e.bank_detail_number,
                    e.amount,
                    e.status,
                    e.exchange_rate,
                )
                .order_by(e.create_timestamp.desc())
            )
            query = query.where(u.user_id == request.user_id)
            if request.role == "team":
                query = query.where(e.team_id == request.user_id)
            if request.role == "merchant":
                query = query.where(e.merchant_id == request.user_id)

            if request.status:
                query = query.where(e.status == request.status)

            if request.amount_from is not None:
                query = query.where(e.amount >= request.amount_from)
            if request.amount_to is not None:
                query = query.where(e.amount <= request.amount_to)

            if request.currency_id:
                query = query.where(e.currency_id == request.currency_id)

            if request.direction:
                query = query.where(e.direction == request.direction)

            if request.create_timestamp_from is not None:
                create_timestamp_from = datetime.fromtimestamp(
                    request.create_timestamp_from
                )
                query = query.where(e.create_timestamp >= create_timestamp_from)
            if request.create_timestamp_to is not None:
                create_timestamp_to = datetime.fromtimestamp(
                    request.create_timestamp_to
                )
                query = query.where(e.create_timestamp <= create_timestamp_to)
            if (
                    request.create_timestamp_from is None
                    and request.create_timestamp_to is None
            ):
                query = query.where(e.create_timestamp >= date_31_days_ago)

            result = await session.execute(query)
            rows = result.all()

            response_list = []
            for row in rows:
                response_list.append(
                    ExportTransactionsResponse(
                        transaction_id=row.transaction_id,
                        merchant_transaction_id=row.merchant_transaction_id,
                        create_timestamp=row.create_timestamp,
                        direction=row.direction,
                        bank_detail_number=row.bank_detail_number,
                        transaction_amount=row.transaction_amount,
                        status=row.status,
                        usdt_deposit_change=row.usdt_deposit_change,
                        exchange_rate=row.exchange_rate,
                        interest=row.interest
                    )
                )

            return response_list

    @staticmethod
    async def filter_inout_cumulative_transactions(
            *, role, balance_id, create_timestamp_from, create_timestamp_to
    ):
        if role == Role.MERCHANT:
            return await TransactionsRepository._filter_for_merchant(
                balance_id=balance_id,
                create_timestamp_from=create_timestamp_from,
                create_timestamp_to=create_timestamp_to,
                role=role
            )
        else:
            return await TransactionsRepository._filter_for_team_or_agent(
                balance_id=balance_id,
                create_timestamp_from=create_timestamp_from,
                create_timestamp_to=create_timestamp_to,
                role=role
            )

    @staticmethod
    async def _filter_for_merchant(*, balance_id, create_timestamp_from, create_timestamp_to, role):
        async with ro_async_session() as session:
            create_timestamp_from = get_create_timestamp_from(create_timestamp_from)
            create_timestamp_to = get_create_timestamp_to(create_timestamp_to)

            subquery = (
                select(
                    UserBalanceChangeModel.transaction_id,
                    func.sum(UserBalanceChangeModel.trust_balance).label("trust_balance"),
                    func.max(UserBalanceChangeModel.create_timestamp).label("max_create_timestamp"),
                )
                .where(UserBalanceChangeModel.balance_id == balance_id)
                .group_by(UserBalanceChangeModel.transaction_id)
                .subquery()
            )

            cumulative_subquery = (
                select(
                    subquery.c.transaction_id,
                    subquery.c.trust_balance,
                    subquery.c.max_create_timestamp,
                    (
                            func.sum(subquery.c.trust_balance)
                            .over(order_by=subquery.c.max_create_timestamp)
                            / ONE_MILLION
                    ).label("cumulative_trust_balance"),
                )
                .subquery()
            )

            stmt = (
                select(
                    UserModel.name,
                    cumulative_subquery.c.transaction_id,
                    ExternalTransactionModel.merchant_transaction_id,
                    ExternalTransactionModel.merchant_payer_id,
                    ExternalTransactionModel.create_timestamp,
                    ExternalTransactionModel.direction,
                    ExternalTransactionModel.bank_detail_number,
                    (ExternalTransactionModel.amount / ONE_MILLION).label("transaction_amount"),
                    ExternalTransactionModel.status,
                    (1.0 * ExternalTransactionModel.exchange_rate / ONE_MILLION).label("exchange_rate"),
                    cumulative_subquery.c.cumulative_trust_balance,
                    cumulative_subquery.c.max_create_timestamp.label("max_create_timestamp"),
                    (cumulative_subquery.c.trust_balance / ONE_MILLION).label("usdt_deposit_change"),
                    case(
                        (ExternalTransactionModel.amount == 0, 0),
                        (ExternalTransactionModel.exchange_rate == 0, 0),
                        (ExternalTransactionModel.status == 'close', 0),
                        else_=func.round(
                            cast(
                                100 * func.abs(
                                    func.abs(
                                        cumulative_subquery.c.trust_balance /
                                        (ExternalTransactionModel.amount / ExternalTransactionModel.exchange_rate)
                                        / ONE_MILLION
                                    ) - (1 if role in [Role.TEAM, Role.MERCHANT] else 0)
                                ),
                                Numeric,
                            ),
                            2,
                        ),
                    ).label("interest"),
                )
                .select_from(cumulative_subquery)
                .join(ExternalTransactionModel, cumulative_subquery.c.transaction_id == ExternalTransactionModel.id,
                      isouter=True)
                .join(UserModel, ExternalTransactionModel.team_id == UserModel.id)
                .where(
                    cumulative_subquery.c.max_create_timestamp >= create_timestamp_from,
                    cumulative_subquery.c.max_create_timestamp <= create_timestamp_to,
                )
                .order_by(cumulative_subquery.c.max_create_timestamp.desc())
            )

            result = await session.execute(stmt)
            rows = result.all()
            existing_transaction_ids = {row.transaction_id for row in rows}

            merchant_ids_subquery = (
                select(UserModel.id)
                .where(UserModel.balance_id == balance_id)
            )

            close_stmt = (
                select(
                    ExternalTransactionModel.id,
                    ExternalTransactionModel.merchant_transaction_id,
                    ExternalTransactionModel.merchant_payer_id,
                    ExternalTransactionModel.create_timestamp,
                    ExternalTransactionModel.direction,
                    ExternalTransactionModel.bank_detail_number,
                    ExternalTransactionModel.amount,
                    ExternalTransactionModel.status,
                    ExternalTransactionModel.exchange_rate,
                    ExternalTransactionModel.final_status_timestamp,
                    ExternalTransactionModel.team_id
                )
                .where(
                    ExternalTransactionModel.status == 'close',
                    ExternalTransactionModel.merchant_id.in_(merchant_ids_subquery),
                    ExternalTransactionModel.id.notin_(existing_transaction_ids),
                    ExternalTransactionModel.final_status_timestamp >= create_timestamp_from,
                    ExternalTransactionModel.final_status_timestamp <= create_timestamp_to,
                )
            )

            close_rows = (await session.execute(close_stmt)).all()

            combined = [
                ExportSumTransactionsResponse(
                    team_name=row.name if role == Role.AGENT else None,
                    transaction_id=row.transaction_id,
                    merchant_transaction_id=row.merchant_transaction_id,
                    merchant_payer_id=row.merchant_payer_id if role == Role.MERCHANT else None,
                    create_timestamp=row.create_timestamp,
                    direction=row.direction,
                    bank_detail_number=row.bank_detail_number,
                    transaction_amount=row.transaction_amount,
                    status_last_update_timestamp=row.max_create_timestamp,
                    status=row.status,
                    usdt_deposit_change=row.usdt_deposit_change,
                    exchange_rate=row.exchange_rate,
                    cumulative_trust_balance=row.cumulative_trust_balance,
                    interest=row.interest,
                )
                for row in rows
            ]

            for row in close_rows:
                combined.append(
                    ExportSumTransactionsResponse(
                        team_name=row.name if role == Role.AGENT else None,
                        transaction_id=row.id,
                        merchant_transaction_id=row.merchant_transaction_id,
                        merchant_payer_id=row.merchant_payer_id if role == Role.MERCHANT else None,
                        create_timestamp=row.create_timestamp,
                        direction=row.direction,
                        bank_detail_number=row.bank_detail_number,
                        transaction_amount=row.amount / ONE_MILLION,
                        status=row.status,
                        status_last_update_timestamp=row.final_status_timestamp,
                        usdt_deposit_change=0,
                        exchange_rate=row.exchange_rate / ONE_MILLION,
                        cumulative_trust_balance=None,
                        interest=0,
                    )
                )

            combined.sort(key=lambda r: r.status_last_update_timestamp)

            prev_cum = 0
            for row in combined:
                if row.cumulative_trust_balance is None:
                    row.cumulative_trust_balance = prev_cum
                else:
                    prev_cum = row.cumulative_trust_balance

            combined.reverse()
            return combined

    @staticmethod
    async def _filter_for_team_or_agent(*, balance_id, create_timestamp_from, create_timestamp_to, role):
        async with ro_async_session() as session:
            create_timestamp_from = get_create_timestamp_from(create_timestamp_from)
            create_timestamp_to = get_create_timestamp_to(create_timestamp_to)

            subquery = (
                select(
                    UserBalanceChangeModel.transaction_id,
                    func.sum(UserBalanceChangeModel.trust_balance).label("trust_balance"),
                    func.max(UserBalanceChangeModel.create_timestamp).label("max_create_timestamp"),
                )
                .where(UserBalanceChangeModel.balance_id == balance_id)
                .group_by(UserBalanceChangeModel.transaction_id)
                .subquery()
            )

            cumulative_subquery = (
                select(
                    subquery.c.transaction_id,
                    subquery.c.trust_balance,
                    subquery.c.max_create_timestamp,
                    (
                            func.sum(subquery.c.trust_balance)
                            .over(order_by=subquery.c.max_create_timestamp)
                            / ONE_MILLION
                    ).label("cumulative_trust_balance"),
                )
                .subquery()
            )

            stmt = (
                select(
                    UserModel.name,
                    cumulative_subquery.c.transaction_id,
                    ExternalTransactionModel.merchant_transaction_id,
                    ExternalTransactionModel.merchant_payer_id,
                    ExternalTransactionModel.create_timestamp,
                    ExternalTransactionModel.direction,
                    ExternalTransactionModel.bank_detail_number,
                    (ExternalTransactionModel.amount / ONE_MILLION).label("transaction_amount"),
                    ExternalTransactionModel.status,
                    (1.0 * ExternalTransactionModel.exchange_rate / ONE_MILLION).label("exchange_rate"),
                    cumulative_subquery.c.cumulative_trust_balance,
                    cumulative_subquery.c.max_create_timestamp.label("max_create_timestamp"),
                    (cumulative_subquery.c.trust_balance / ONE_MILLION).label("usdt_deposit_change"),
                    case(
                        (ExternalTransactionModel.amount == 0, 0),
                        (ExternalTransactionModel.exchange_rate == 0, 0),
                        (ExternalTransactionModel.status == 'close', None),
                        else_=func.round(
                            cast(
                                100 * func.abs(
                                    func.abs(
                                        cumulative_subquery.c.trust_balance /
                                        (ExternalTransactionModel.amount / ExternalTransactionModel.exchange_rate)
                                        / ONE_MILLION
                                    ) - (1 if role in [Role.TEAM, Role.MERCHANT] else 0)
                                ),
                                Numeric,
                            ),
                            2,
                        ),
                    ).label("interest"),
                )
                .select_from(cumulative_subquery)
                .join(ExternalTransactionModel, cumulative_subquery.c.transaction_id == ExternalTransactionModel.id,
                      isouter=True)
                .join(UserModel, ExternalTransactionModel.team_id == UserModel.id)
                .where(
                    cumulative_subquery.c.max_create_timestamp >= create_timestamp_from,
                    cumulative_subquery.c.max_create_timestamp <= create_timestamp_to,
                )
                .order_by(cumulative_subquery.c.max_create_timestamp.desc())
            )

            result = await session.execute(stmt)
            rows = result.all()

            return [
                ExportSumTransactionsResponse(
                    team_name=row.name if role == Role.AGENT else None,
                    transaction_id=row.transaction_id,
                    merchant_transaction_id=row.merchant_transaction_id,
                    merchant_payer_id=row.merchant_payer_id if role == Role.MERCHANT else None,
                    create_timestamp=row.create_timestamp,
                    direction=row.direction,
                    bank_detail_number=row.bank_detail_number,
                    transaction_amount=row.transaction_amount,
                    status_last_update_timestamp=row.max_create_timestamp,
                    status=row.status,
                    usdt_deposit_change=row.usdt_deposit_change,
                    exchange_rate=row.exchange_rate,
                    cumulative_trust_balance=row.cumulative_trust_balance,
                    interest=row.interest,
                )
                for row in rows
            ]

    @measure_exe_time
    @staticmethod
    async def filter_internal_transactions_for_export(
            request: ExportInternalTransactionsRequest,
    ) -> List[ExportInternalTransactionsResponse]:
        async with ro_async_session() as session:
            i = aliased(InternalTransactionModel)
            um = aliased(UserModel)

            # Берем дату 31 день назад от текущей даты, включая сегодняший день
            date_31_days_ago = datetime.utcnow().replace(
                hour=23, minute=59, second=59, microsecond=0
            ) - timedelta(days=31)

            query = (
                select(
                    i.id,
                    i.create_timestamp,
                    i.address,
                    i.blockchain_transaction_hash,
                    um.name,
                    (i.amount / ONE_MILLION).label("transaction_amount"),
                )
                .join(um, i.user_id == um.id)
                .where(i.create_timestamp >= date_31_days_ago, )
                .group_by(
                    i.id,
                    i.create_timestamp,
                    i.address,
                    i.blockchain_transaction_hash,
                    um.name,
                    i.amount,
                )
                .order_by(um.name ,i.create_timestamp)
            )


            namespace_query = await session.execute(
                select(um.namespace_id).where(um.id == request.user_id)
            )
            namespace_id = namespace_query.scalar()
            query = query.where(um.id == request.user_id if request.role == Role.TEAM or request.role == Role.MERCHANT else true())
            query = query.where(um.namespace_id == namespace_id)
            if request.status is not None:
                query = query.where(i.status == request.status)
            if request.amount_from is not None:
                query = query.where(i.amount / ONE_MILLION >= request.amount_from)
            if request.amount_to is not None:
                query = query.where(i.amount / ONE_MILLION <= request.amount_to)
            if request.direction is not None:
                query = query.where(i.direction == request.direction)

            result = await session.execute(query)
            rows = result.all()

            response_list = []
            for row in rows:
                response_list.append(
                    ExportInternalTransactionsResponse(
                        create_timestamp=row.create_timestamp,
                        name=row.name,
                        amount=row.transaction_amount,
                        address=row.address,
                        blockchain_transaction_hash=row.blockchain_transaction_hash,
                    )
                )

            return response_list


    @staticmethod
    async def batched_transactions_generator(
            balance_id: str,
            role: str,
            from_ts: int,
            to_ts: int,
    ):
        BATCH_SIZE = 30000
        offset = 0
        prev_cum = 0

        while True:
            rows = await TransactionsRepository._fetch_transaction_batch(
                balance_id=balance_id,
                role=role,
                offset=offset,
                limit=BATCH_SIZE,
                from_ts=from_ts,
                to_ts=to_ts,
            )

            if not rows:
                break

            rows.sort(key=lambda row: row.status_last_update_timestamp, reverse=True)

            for row in rows:
                yield row

            offset += BATCH_SIZE


    @staticmethod
    async def _fetch_transaction_batch(
            balance_id: str,
            role: str,
            offset: int,
            limit: int,
            from_ts: int,
            to_ts: int
    ):
        async with ro_async_session() as session:
            create_timestamp_from = get_create_timestamp_from(from_ts)
            create_timestamp_to = get_create_timestamp_to(to_ts)

            subquery = (
                select(
                    UserBalanceChangeModel.transaction_id,
                    func.sum(UserBalanceChangeModel.trust_balance).label("trust_balance"),
                    func.max(UserBalanceChangeModel.create_timestamp).label("max_create_timestamp"),
                )
                .where(UserBalanceChangeModel.balance_id == balance_id)
                .group_by(UserBalanceChangeModel.transaction_id)
                .subquery()
            )

            cumulative_subquery = (
                select(
                    subquery.c.transaction_id,
                    subquery.c.trust_balance,
                    subquery.c.max_create_timestamp,
                    (
                            func.sum(subquery.c.trust_balance)
                            .over(order_by=subquery.c.max_create_timestamp)
                            / ONE_MILLION
                    ).label("cumulative_trust_balance"),
                )
                .subquery()
            )

            with_trust_stmt = (
                select(
                    UserModel.name,
                    cumulative_subquery.c.transaction_id,
                    ExternalTransactionModel.merchant_transaction_id,
                    ExternalTransactionModel.merchant_payer_id,
                    ExternalTransactionModel.create_timestamp,
                    ExternalTransactionModel.direction,
                    ExternalTransactionModel.bank_detail_number,
                    (ExternalTransactionModel.amount / ONE_MILLION).label("transaction_amount"),
                    ExternalTransactionModel.status,
                    (ExternalTransactionModel.exchange_rate / ONE_MILLION).label("exchange_rate"),
                    cumulative_subquery.c.cumulative_trust_balance,
                    cumulative_subquery.c.max_create_timestamp.label("status_last_update_timestamp"),
                    (cumulative_subquery.c.trust_balance / ONE_MILLION).label("usdt_deposit_change"),
                    case(
                        (ExternalTransactionModel.amount == 0, 0),
                        (ExternalTransactionModel.exchange_rate == 0, 0),
                        (ExternalTransactionModel.status == 'close', 0),
                        else_=func.round(
                            cast(
                                100 * func.abs(
                                    func.abs(
                                        cumulative_subquery.c.trust_balance /
                                        (ExternalTransactionModel.amount / ExternalTransactionModel.exchange_rate)
                                        / ONE_MILLION
                                    ) - (1 if role in [Role.TEAM, Role.MERCHANT] else 0)
                                ),
                                Numeric,
                            ),
                            2,
                        ),
                    ).label("interest"),
                )
                .select_from(cumulative_subquery)
                .join(ExternalTransactionModel, cumulative_subquery.c.transaction_id == ExternalTransactionModel.id, isouter=True)
                .join(UserModel, ExternalTransactionModel.merchant_id == UserModel.id if role == Role.MERCHANT else ExternalTransactionModel.team_id == UserModel.id, isouter=True)
                .where(
                    cumulative_subquery.c.max_create_timestamp >= create_timestamp_from,
                    cumulative_subquery.c.max_create_timestamp <= create_timestamp_to,
                )
                .order_by(cumulative_subquery.c.max_create_timestamp.desc())
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(with_trust_stmt)
            trust_rows = result.all()
            existing_transaction_ids = {row.transaction_id for row in trust_rows}

            merchant_ids_subquery = (
                select(UserModel.id)
                .where(UserModel.balance_id == balance_id)
            )

            close_stmt = (
                select(
                    ExternalTransactionModel.id,
                    ExternalTransactionModel.merchant_transaction_id,
                    ExternalTransactionModel.merchant_payer_id,
                    ExternalTransactionModel.create_timestamp,
                    ExternalTransactionModel.direction,
                    ExternalTransactionModel.bank_detail_number,
                    ExternalTransactionModel.amount,
                    ExternalTransactionModel.status,
                    ExternalTransactionModel.exchange_rate,
                    ExternalTransactionModel.final_status_timestamp.label("status_last_update_timestamp"),
                    ExternalTransactionModel.team_id,
                    UserModel.name,
                )
                .join(UserModel, ExternalTransactionModel.merchant_id == UserModel.id if role == Role.MERCHANT else ExternalTransactionModel.team_id == UserModel.id)
                .where(
                    ExternalTransactionModel.status == 'close',
                    ExternalTransactionModel.merchant_id.in_(merchant_ids_subquery),
                    ExternalTransactionModel.final_status_timestamp >= create_timestamp_from,
                    ExternalTransactionModel.final_status_timestamp <= create_timestamp_to,
                    ExternalTransactionModel.id.notin_(existing_transaction_ids),
                )
                .order_by(ExternalTransactionModel.final_status_timestamp.desc())
                .limit(limit)
                .offset(offset)
            )

            close_result = await session.execute(close_stmt)
            close_rows = close_result.all()

            return [
                ExportSumTransactionsResponse(
                    token_name=row.name if role == Role.MERCHANT else None,
                    team_name=row.name if role == Role.AGENT else None,
                    transaction_id=row.transaction_id,
                    merchant_transaction_id=row.merchant_transaction_id,
                    merchant_payer_id=row.merchant_payer_id if role == Role.MERCHANT else None,
                    create_timestamp=row.create_timestamp,
                    direction="settlement" if row.direction is None else row.direction,
                    bank_detail_number=row.bank_detail_number,
                    transaction_amount=row.transaction_amount,
                    status=row.status,
                    status_last_update_timestamp=row.status_last_update_timestamp,
                    usdt_deposit_change=row.usdt_deposit_change,
                    exchange_rate=row.exchange_rate,
                    cumulative_trust_balance=0 if row.status == 'close' else row.cumulative_trust_balance,
                    interest=row.interest,
                )
                for row in trust_rows
            ] + [
                ExportSumTransactionsResponse(
                    token_name=row.name if role == Role.MERCHANT else None,
                    team_name=row.name if role == Role.AGENT else None,
                    transaction_id=row.id,
                    merchant_transaction_id=row.merchant_transaction_id,
                    merchant_payer_id=row.merchant_payer_id if role == Role.MERCHANT else None,
                    create_timestamp=row.create_timestamp,
                    direction=row.direction,
                    bank_detail_number=row.bank_detail_number,
                    transaction_amount=row.amount / ONE_MILLION,
                    status=row.status,
                    status_last_update_timestamp=row.status_last_update_timestamp,
                    usdt_deposit_change=0,
                    exchange_rate=row.exchange_rate / ONE_MILLION,
                    cumulative_trust_balance=0,
                    interest=0,
                )
                for row in close_rows
            ]


