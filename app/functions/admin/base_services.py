from typing import List

from sqlalchemy import and_, delete, select

from app import exceptions
from app.core.constants import Role
from app.core.security import generate_password, get_password_hash
from app.core.session import async_session
from app.exceptions import UserNotFoundException, NotUniqueUserName
from app.functions.balance import add_balance_changes, get_balances
from app.functions.user import user_get_by_id
from app.models import FeeContractModel, UserModel, TagModel
from app.schemas.admin.FeeContractScheme import FeeContractResponse, FeeContractBatchRequest
from app.schemas.UserScheme import UserSchemeRequestGetById
from app.utils.session import get_session


async def validate_participants_belong_to_namespace(
    *, merchant_id: str, team_id: str, namespace: str
):
    if merchant_id:
        merchant = await user_get_by_id(UserSchemeRequestGetById(id=merchant_id))
        if (
            merchant is None or merchant.role != Role.MERCHANT
        ) and merchant.namespace != namespace:
            raise UserNotFoundException()
    if team_id:
        team = await user_get_by_id(UserSchemeRequestGetById(id=team_id))
        if (team is None or team.role != Role.TEAM) and team.namespace != namespace:
            raise UserNotFoundException()


async def batch_create_fee_contracts_service(
    *, merchant_id: str, team_id: str, tag_id: str, fee_contracts: List[FeeContractBatchRequest]
):
    async with async_session() as session:
        ids: list[str] = [i.user_id for i in fee_contracts]
        roles_by_ids_q = await session.execute(
            select(UserModel.role).filter(UserModel.id.in_(ids))
        )
        roles_by_ids: list[str] = [i[0] for i in roles_by_ids_q.fetchall()]
        merchants_count = roles_by_ids.count(Role.MERCHANT)
        teams_count = roles_by_ids.count(Role.TEAM)
        if teams_count != 1 or merchants_count != 1:
            raise exceptions.OnlyOneMerchantTeamException()
        await session.execute(
            delete(FeeContractModel).where(
                and_(
                    FeeContractModel.merchant_id == merchant_id,
                    FeeContractModel.team_id == team_id,
                    FeeContractModel.tag_id == tag_id
                )
            )
        )
        name_q = await session.execute(
            select(UserModel.name).where(UserModel.id == merchant_id)
        )
        merchant_name = name_q.scalar()
        name_q = await session.execute(
            select(UserModel.name).where(UserModel.id == team_id)
        )
        team_name = name_q.scalar()
        print([c.__dict__ for c in fee_contracts])
        new_contracts = []
        for contract in fee_contracts:
            user_id = contract.user_id
            name_q = await session.execute(
                select(UserModel.name).where(UserModel.id == user_id)
            )
            user_name = name_q.scalar()
            name_q = await session.execute(
                select(TagModel.name).where(TagModel.id == tag_id)
            )
            tag_name = name_q.scalar()
            new_contract = FeeContractModel(
                merchant_id=merchant_id,
                team_id=team_id,
                **contract.__dict__,
                comment=f"{tag_name}: {merchant_name} <-> {team_name} -> {user_name}",
                is_deleted=False,
                tag_id=tag_id
            )
            new_contracts.append(new_contract)
        session.add_all(new_contracts)
        await session.commit()


async def validate_unique_user(session, *, name: str, namespace_id: int):
    async with get_session(session) as session:
        stmt = select(UserModel).filter_by(name=name, namespace_id=namespace_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            raise NotUniqueUserName(name)


async def validate_user_has_role(*, session=None, user_id: str, role: str):
    async with get_session(session) as session:
        stmt = select(UserModel).filter_by(id=user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user.role != role:
            raise ValueError("User has incorrect role.")


class BaseCreateService:
    async def execute(self, *, name: str, namespace: str, **kwargs):
        async with get_session() as session:
            async with session.begin():
                await validate_unique_user(session, name=name, namespace=namespace)
                user, credentials = await self._create(
                    session=session, name=name, namespace=namespace, **kwargs
                )

                await add_balance_changes(
                    session,
                    [
                        {
                            "user_id": user.id,
                            "balance_id": user.balance_id,
                        }
                    ],
                )
                balances = await get_balances(user.id, session)

                user = await self._get(user_id=user.id, session=session, **kwargs)

                update = {
                    **credentials,
                    "trust_balance": balances[0],
                    "locked_balance": balances[1],
                    "profit_balance": balances[2],
                    "fiat_trust_balance": balances[3],
                    "fiat_locked_balance": balances[4],
                    "fiat_profit_balance": balances[5],
                }

                user = user.model_copy(update=update)

                await session.commit()

                return user

    async def _create(self, *, session, name, namespace, role, **kwargs):
        async with get_session(session) as session:
            password = generate_password()
            api_secret = generate_password()
            user_model: UserModel = UserModel(
                name=name,
                namespace=namespace,
                role=role,
                password_hash=get_password_hash(password),
                api_secret=api_secret,
                is_enabled=False,
                is_blocked=False,
                **kwargs,
            )
            session.add(user_model)
            await session.flush()

            user_model.balance_id = user_model.id
            return user_model, {"password": password, "api_secret": api_secret}

    async def _get(self, *, session, user_id: str, **kwargs):
        user = await self.repo.get(session, user_id=user_id)
        return user

#import asyncio
#
#async def main():
#    async with async_session() as session:
#        result = await session.execute(select(FeeContractModel))
#        fee_contracts = result.scalars().all()
#        print(len(fee_contracts))
#        for contract in fee_contracts:
#            merchant_id = contract.merchant_id
#            team_id = contract.team_id
#            user_id = contract.user_id
#            tag_id = contract.tag_id
#
#            name_q = await session.execute(
#                select(TagModel.name).where(TagModel.id == tag_id)
#            )
#            tag_name = name_q.scalar()
#
#            name_q = await session.execute(
#                select(UserModel.name).where(UserModel.id == merchant_id)
#            )
#            merchant_name = name_q.scalar()
#
#            name_q = await session.execute(
#                select(UserModel.name).where(UserModel.id == team_id)
#            )
#            team_name = name_q.scalar()
#
#            name_q = await session.execute(
#                select(UserModel.name).where(UserModel.id == user_id)
#            )
#            user_name = name_q.scalar()
#
#            contract.comment = f"{tag_name}: {merchant_name} <-> {team_name} -> {user_name}"
#            print(f"{tag_name}: {merchant_name} <-> {team_name} -> {user_name}")
#
#       await session.commit()
#
#
#if __name__ == '__main__':
#    asyncio.run(main())