import asyncio
from typing import List

from sqlalchemy import func, select, update, true, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.constants import Status
from app.models import (
    ExternalTransactionModel,
    UserBalanceChangeNonceModel,
    TeamModel,
    UserModel
)
from app.schemas.admin.TeamScheme import V2TeamResponseScheme
from app.schemas.UserScheme import UserTeamScheme, get_user_scheme
from app.utils.session import get_session
from app.functions.balance import get_balances_for_multiple_ids


class AdminTeamRepo:

    @classmethod
    async def get(
            cls, session: AsyncSession, team_id: str
    ) -> V2TeamResponseScheme | None:
        async with get_session(session) as session:
            today_outbound_amount_case = case(
                (func.date(TeamModel.last_transaction_timestamp) < func.date(func.now()), 0),
                else_=TeamModel.today_outbound_amount_used
            ).label("today_outbound_amount_used")

            query = (select(TeamModel, today_outbound_amount_case).filter(team_id == TeamModel.id))
            result = await session.execute(query)
            row = result.one()

            if not row:
                return None

            user_row, today_outbound_amount_used = row
            team = get_user_scheme(user_row)

            balance_data = await get_balances_for_multiple_ids(session, [team.balance_id])
            balance_values = balance_data.get(team.balance_id, [0, 0, 0, 0, 0, 0])

            pay_in, pay_out = (
                await cls._calculate_per_ext_trans(session, team_id)
            )

            data = {
                **{k: v for k, v in team.dict().items() if k not in {"api_secret", "today_outbound_amount_used"}},
                "trust_balance": balance_values[0],
                "locked_balance": balance_values[1],
                "profit_balance": balance_values[2],
                "fiat_trust_balance": balance_values[3],
                "fiat_locked_balance": balance_values[4],
                "fiat_profit_balance": balance_values[5],
                "pay_in": pay_in,
                "pay_out": pay_out,
                "today_outbound_amount_used": today_outbound_amount_used,
            }

            return V2TeamResponseScheme.model_validate(data)

    @classmethod
    async def list(
        cls, *, session: AsyncSession, geo_id: int | None, namespace_id: int, search: str | None, **kwargs
    ) -> List[V2TeamResponseScheme]:
        async with get_session(session) as session:
            today_outbound_amount_case = case(
                (func.date(TeamModel.last_transaction_timestamp) < func.date(func.now()), 0),
                else_=TeamModel.today_outbound_amount_used
            ).label("today_outbound_amount_used")

            query = (
                select(TeamModel, today_outbound_amount_case)
                .filter(
                    TeamModel.namespace_id == namespace_id,
                    true() if geo_id is None else TeamModel.geo_id == geo_id,
                    true() if search is None else TeamModel.name.ilike(f"%{search}%"),
                )
                .order_by(
                    TeamModel.is_blocked,
                    case((TeamModel.is_inbound_enabled == True, 1), else_=0).desc(),
                    case((TeamModel.is_outbound_enabled == True, 1), else_=0).desc(),
                    TeamModel.name
                )
            )

            result = await session.execute(query)
            user_rows = result.all()

            if not user_rows:
                return []

            balance_ids = [row.balance_id for row, _ in user_rows]
            balances = await get_balances_for_multiple_ids(session, balance_ids)
            team_ids = [row.id for row, _ in user_rows]

            transaction_query = (
                select(
                    ExternalTransactionModel.team_id,
                    func.count().filter(
                        ExternalTransactionModel.direction == "inbound",
                        ExternalTransactionModel.status == Status.PENDING
                    ).label("pay_in"),
                    func.count().filter(
                        ExternalTransactionModel.direction == "outbound",
                        ExternalTransactionModel.status == Status.PENDING
                    ).label("pay_out")
                )
                .filter(ExternalTransactionModel.team_id.in_(team_ids))
                .group_by(ExternalTransactionModel.team_id)
            )
            transaction_result = await session.execute(transaction_query)
            transaction_rows = transaction_result.fetchall()
            transaction_data = {
                row.team_id: {"pay_in": row.pay_in, "pay_out": row.pay_out}
                for row in transaction_rows
            }
            results = []
            for row, today_outbound_amount_used in user_rows:
                team_data = row.__dict__
                team_id = row.id

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
                pay_in = transaction_data.get(team_id, {}).get("pay_in", 0)
                pay_out = transaction_data.get(team_id, {}).get("pay_out", 0)
                data = {
                    **{k: v for k, v in team_data.items() if k not in {"api_secret", "today_outbound_amount_used"}},
                    **balance_data,
                    "pay_in": pay_in,
                    "pay_out": pay_out,
                    "today_outbound_amount_used": today_outbound_amount_used,
                }
                results.append(V2TeamResponseScheme.model_validate(data))
            return results

    @classmethod
    async def _calculate_per_ext_trans(cls, session: AsyncSession, team_id: str):
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
                    inbound_trans.team_id == team_id,
                )
                .label("pay_in_1")
            )
            .select_from(TeamModel)
            .outerjoin(
                inbound_trans,
                inbound_trans.team_id == TeamModel.id,
            )
            .where(TeamModel.id == team_id)
        )

        # Pay out ExternalTransactionModel
        pay_out_query_1 = (
            select(
                func.count(outbound_trans.id)
                .filter(
                    outbound_trans.direction == "outbound",
                    outbound_trans.status == Status.PENDING,
                    outbound_trans.team_id == team_id,
                )
                .label("pay_out_1")
            )
            .select_from(TeamModel)
            .outerjoin(
                outbound_trans,
                outbound_trans.team_id == TeamModel.id,
            )
            .where(TeamModel.id == team_id)
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
            team = (await session.execute(
                select(TeamModel)
                .where(user_id == TeamModel.id)
            )).scalar_one_or_none()

            if team is None:
                return None

            for key, value in kwargs.items():
                if hasattr(team, key):
                    setattr(team, key, value)

            await session.commit()
            return await cls.get(session=session, team_id=user_id)
