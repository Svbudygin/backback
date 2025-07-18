from typing import Dict, List, Tuple

from app.functions.admin.base_services import (
    validate_unique_user,
    validate_user_has_role,
)

from app import exceptions
from app.functions.balance import add_balance_changes, get_balances
from app.core.constants import Role
from app.models import UserModel, FeeContractModel
from app.core.security import generate_password, get_password_hash
from app.repositories.admin.agent_repo import AgentRepo
from app.schemas.admin.AgentScheme import AgentResponseScheme, V2AgentResponseScheme
from app.utils.session import get_session, async_session
from app.core.session import ro_async_session
from sqlalchemy import select, update

async def create_agent_user(
        session, name: str, namespace_id: int
) -> Tuple[UserModel, Dict]:
    async with get_session(session) as session:
        password = generate_password()

        user_model = UserModel(
            password_hash=get_password_hash(password),
            name=name,
            role=Role.AGENT,
            is_blocked=False,
            namespace_id=namespace_id,
        )

        session.add(user_model)
        await session.flush()

        user_model.balance_id = user_model.id
        return user_model, {"password": password}


async def create_and_get_agent_user(
        session, name: str, namespace_id: int
):
    async with get_session(session) as session:
        async with session.begin():
            await validate_unique_user(session, name=name, namespace_id=namespace_id)

            user, credentials = await create_agent_user(
                session,
                name=name,
                namespace_id=namespace_id
            )

            await add_balance_changes(
                session,
                [
                    {
                        "user_id": user.id,
                        "balance_id": user.balance_id
                    }
                ],
            )
            balances = await get_balances(user.id, session)

            agent_user: V2AgentResponseScheme = await AgentRepo.get(
                session, agent_id=user.id
            )

            update = {
                **credentials,
                "trust_balance": balances[0],
                "locked_balance": balances[1],
                "profit_balance": balances[2],
                "fiat_trust_balance": balances[3],
                "fiat_locked_balance": balances[4],
                "fiat_profit_balance": balances[5],
            }

            agent_user = agent_user.model_copy(update=update)

            await session.commit()

            return agent_user


async def list_agent_users(
    *, session=None, namespace_id: int
) -> List[V2AgentResponseScheme]:
    async with ro_async_session() as session:
        users: List[V2AgentResponseScheme] = await AgentRepo.list(
            session=session, namespace_id=namespace_id
        )
        return users


async def update_agent_user(session=None, **kwargs) -> V2AgentResponseScheme:
    async with get_session(session) as session:
        await validate_user_has_role(
            session=session, user_id=kwargs["user_id"], role=kwargs["role"]
        )

        if kwargs.get("is_blocked") is True:
            has_fee_query = select(FeeContractModel).where(
                FeeContractModel.user_id == kwargs["user_id"],
                FeeContractModel.is_deleted == False
            )
            result = await session.execute(has_fee_query)
            contracts = result.scalars().all()
            if contracts:
                raise exceptions.DeleteFeeContractsToBlock()

        user = await AgentRepo.update(session=session, **kwargs)
        return user

async def regenerate_agent_user(agent_id: str) -> V2AgentResponseScheme:
    async with async_session() as session:
            agent_user: V2AgentResponseScheme = await AgentRepo.get(session, agent_id=agent_id)
            model_user = await session.execute(select(UserModel).where(UserModel.id == agent_id))
            model_user = model_user.scalar_one()
            password = generate_password()
            hash = get_password_hash(password)
            credentials = {
                "password_hash": hash,
            }
            model_user.password_hash = hash
            await session.flush()
            update = {
                **credentials,
                "password": password
            }
            updated_agent_user = agent_user.model_copy(update=update)
            await session.commit()
            return updated_agent_user
