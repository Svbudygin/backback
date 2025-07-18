from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.models import UserModel, UserBalanceChangeNonceModel
from app.schemas.admin.AgentScheme import V2AgentResponseScheme
from app.schemas.UserScheme import get_user_scheme
from app.utils.session import get_session
from app.functions.balance import get_balances_for_multiple_ids


class AgentRepo:
    @classmethod
    async def get(
            cls, session: AsyncSession, agent_id: str
    ) -> V2AgentResponseScheme | None:
        async with get_session(session) as session:
            query = (
                select(UserModel)
                .filter(
                    UserModel.role == Role.AGENT,
                    UserModel.id == agent_id
                )
            )

            result = await session.execute(query)
            user_row = result.scalar_one_or_none()

            if not user_row:
                return None

            balance_ids = [user_row.balance_id]
            balances = await get_balances_for_multiple_ids(session, balance_ids)
            balance_data = balances.get(user_row.balance_id)

            if not balance_data:
                return V2AgentResponseScheme.model_validate(user_row)

            user_row_dict = {key: value for key, value in vars(user_row).items() if not key.startswith('_')}


            data = {
                "trust_balance": balance_data[0],
                **user_row_dict,
            }

            return V2AgentResponseScheme.model_validate(data)

    @classmethod
    async def list(
        cls, *, session: AsyncSession, namespace_id: int
    ) -> List[V2AgentResponseScheme | None]:
        async with get_session(session) as session:
            stmt = (
                select(UserModel)
                .select_from(UserModel)
                .where(UserModel.role == Role.AGENT)
                .where(UserModel.namespace_id == namespace_id)
                .order_by(UserModel.is_blocked)
            )

            result = await session.execute(stmt)
            user_rows = [get_user_scheme(item) for item in result.scalars().all()]
            balance_ids = [r.balance_id for r in user_rows]
            balances = await get_balances_for_multiple_ids(session, balance_ids)
            results = []
            for row in user_rows:
                if row is None:
                    continue
                balance_data = balances.get(row.balance_id)

                if balance_data is None:
                    data = {
                        **row.model_dump(),
                    }

                    results.append(V2AgentResponseScheme.model_validate(data))

                    continue

                data = {
                    "trust_balance": balance_data[0],
                    **row.model_dump()
                }

                results.append(V2AgentResponseScheme.model_validate(data))
            return results

    @classmethod
    async def update(cls, *, session: AsyncSession = None, user_id: str, **kwargs):
        async with get_session(session) as session:
            stmt = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(
                    {key: value for key, value in kwargs.items() if value is not None}
                )
            )
            await session.execute(stmt)
            await session.commit()

            return await cls.get(session=session, agent_id=user_id)
