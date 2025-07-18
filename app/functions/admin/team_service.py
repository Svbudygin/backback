from typing import Dict, List, Tuple

from app.core.security import generate_password, get_password_hash
from app.core.session import ro_async_session
from app.functions.admin.base_services import (
    validate_unique_user,
    validate_user_has_role,
)
from app.functions.balance import add_balance_changes, get_balances
from app.models import UserModel, TeamModel, MerchantModel, FeeContractModel, TrafficWeightContractModel, BankDetailModel
from app.repositories.admin.team_repo import AdminTeamRepo
from app.schemas.admin.TeamScheme import TeamResponseScheme, InfoBalanceScheme, V2TeamResponseScheme
from app.schemas.UserScheme import UserTeamScheme
from app.utils.session import get_session, async_session
from app.core.constants import Role
from sqlalchemy import select, update


async def get_economic_model_by_namespace(namespace_id: int) -> str | None:
    async with ro_async_session() as session:
        query = (
            select(
                TeamModel.economic_model
            ).filter(
                TeamModel.namespace_id == namespace_id
            ).order_by(TeamModel.economic_model)
        )

        result = await session.execute(query)
        first_row = result.fetchone()
        return first_row[0] if first_row else None


async def create_team_user(
        session,
        name: str,
        namespace_id: int,
        credit_factor: int,
        balance_id: str | None,
        geo_id: int
) -> Tuple[UserModel, Dict]:
    async with get_session(session) as session:
        password = generate_password()
        api_secret = generate_password()

        team_model = TeamModel(
            password_hash=get_password_hash(password),
            name=name,
            role=Role.TEAM,
            is_blocked=False,
            namespace_id=namespace_id,
            credit_factor=credit_factor,
            api_secret=api_secret,
            is_inbound_enabled=False,
            is_outbound_enabled=False,
            geo_id=geo_id
        )

        session.add(team_model)
        await session.flush()

        team_model.balance_id = team_model.id if balance_id is None else balance_id
        return team_model, {"password": password, "api_secret": api_secret}


async def create_and_get_team_user(
        session,
        name: str,
        namespace_id: int,
        credit_factor: int,
        balance_id: str | None,
        geo_id: int
):
    async with get_session(session) as session:
        async with session.begin():
            await validate_unique_user(session, name=name, namespace_id=namespace_id)
            user, credentials = await create_team_user(
                session,
                name=name,
                namespace_id=namespace_id,
                credit_factor=credit_factor,
                balance_id=balance_id,
                geo_id=geo_id
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

            team_user: UserTeamScheme = await AdminTeamRepo.get(
                session, team_id=user.id
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

            team_user = team_user.model_copy(update=update)

            await session.commit()

            return team_user


async def list_team_users(
        *, session=None, geo_id: int, namespace_id: int, limit: int, last_offset_id: int, search: str | None
) -> List[V2TeamResponseScheme]:
    async with ro_async_session() as session:
        team_users: List[V2TeamResponseScheme] = await AdminTeamRepo.list(
            session=session, geo_id=geo_id, namespace_id=namespace_id, limit=limit, last_offset_id=last_offset_id, search=search
        )
        return team_users


async def list_users_balance_info(
        geo_id: int | None, namespace_id: int, role: str
) -> List[InfoBalanceScheme]:
    async with ro_async_session() as session:
        if Role.TEAM == role:
            if geo_id is None:
                return []
            query = (
                select(
                    UserModel.name,
                    UserModel.balance_id
                ).distinct().join(
                    TeamModel, TeamModel.id == UserModel.id
                ).filter(
                    geo_id == TeamModel.geo_id,
                    role == UserModel.role,
                    False == UserModel.is_blocked,
                    UserModel.id == UserModel.balance_id,
                    namespace_id == UserModel.namespace_id,
                )
            )
            result = await session.execute(query)
            teams_info = result.fetchall()
            res = []
            for row in teams_info:
                res.append(InfoBalanceScheme(name=row.name, balance_id=row.balance_id))
        if Role.MERCHANT == role:
            query = (
                select(
                    UserModel.name,
                    UserModel.balance_id
                ).distinct().join(
                    MerchantModel, MerchantModel.id == UserModel.id
                ).filter(
                    geo_id == MerchantModel.geo_id if geo_id is not None else True,
                    role == UserModel.role,
                    False == UserModel.is_blocked,
                    UserModel.id == UserModel.balance_id,
                    namespace_id == UserModel.namespace_id,
                )
            )
            result = await session.execute(query)
            teams_info = result.fetchall()
            res = []
            for row in teams_info:
                res.append(InfoBalanceScheme(name=row.name, balance_id=row.balance_id))
        return res


async def update_team_user(session=None, **kwargs) -> V2TeamResponseScheme:
    async with get_session(session) as session:
        if kwargs.get("is_blocked") is True:
            upd_query1 = (
                update(FeeContractModel)
                .where(
                    FeeContractModel.team_id == kwargs["user_id"],
                    FeeContractModel.is_deleted == False
                )
                .values(is_deleted=True)
            )
            await session.execute(upd_query1)
            upd_query2 = (
                update(TrafficWeightContractModel)
                .where(
                    TrafficWeightContractModel.team_id == kwargs["user_id"],
                    TrafficWeightContractModel.is_deleted == False
                )
                .values(is_deleted=True)
            )
            await session.execute(upd_query2)
            upd_query3 = (
                update(BankDetailModel)
                .where(
                    BankDetailModel.team_id == kwargs["user_id"],
                    BankDetailModel.is_deleted == False
                )
                .values(is_deleted=True)
            )
            await session.execute(upd_query3)
            await session.commit()
        return await AdminTeamRepo.update(session=session, **kwargs)

async def regenerate_team_user(team_id: str) -> V2TeamResponseScheme:
    async with async_session() as session:
            team_user: V2TeamResponseScheme = await AdminTeamRepo.get(session, team_id=team_id)
            model_user = await session.execute(select(UserModel).where(UserModel.id == team_id))
            model_user = model_user.scalar_one()
            model_team = await session.execute(select(TeamModel).where(TeamModel.id == team_id))
            model_team = model_team.scalar_one()
            password = generate_password()
            hash = get_password_hash(password)
            api_secret = generate_password()
            credentials = {
                "password_hash": hash,
                "api_secret": api_secret
            }
            model_user.password_hash = hash
            model_team.api_secret = api_secret
            await session.flush()
            update = {
                **credentials,
                "password": password
            }
            updated_team_user = team_user.model_copy(update=update)
            await session.commit()
            return updated_team_user
