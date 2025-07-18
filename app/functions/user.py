import asyncio

from sqlalchemy import select, union_all
from sqlalchemy.orm import selectinload, with_polymorphic
from sqlalchemy.ext.asyncio import AsyncSession

from app import exceptions
from app.core.constants import Direction, EconomicModel, Role
from app.core.security import generate_password, get_password_hash
from app.core.session import async_session, ro_async_session
from app.functions.balance import get_balances
from app.models import RoleModel, PermissionModel, TeamModel, MerchantModel
from app.schemas.UserScheme import *


# -----------------------------------------------CREATE--------------------------------------------
async def create_system_user(name: str, role: str) -> str | None:
    async with async_session() as session:
        query_user = await session.execute(
            select(UserModel).where(UserModel.role == role)
        )
        r = query_user.scalars().first()
        if r is not None:
            return None
        
        password = generate_password()
        root_model: UserModel = UserModel(
            password_hash=get_password_hash(password),
            name=name,
            role=role,
            is_enabled=False,
            is_blocked=False,
            trust_balance=0,
            profit_balance=0,
        )
        session.add(root_model)
        await session.commit()
        
        return password


async def create_root_if_not_exist(
        user_scheme_create_root: UserSchemeRequestCreateRoot,
) -> str | None:
    return await create_system_user(user_scheme_create_root.name, Role.ROOT)


async def create_c_worker_if_not_exist(
        user_scheme_create_c_worker: UserSchemeRequestCreateCWorker,
) -> str | None:
    return await create_system_user(user_scheme_create_c_worker.name, Role.C_WORKER)


async def create_b_worker_if_not_exist(
        user_scheme_create_b_worker: UserSchemeRequestCreateBWorker,
) -> str | None:
    return await create_system_user(user_scheme_create_b_worker.name, Role.B_WORKER)


async def create_tv_worker_if_not_exist(
        user_scheme_create_tv_worker: UserSchemeRequestCreateTVWorker,
) -> str | None:
    return await create_system_user(user_scheme_create_tv_worker.name, Role.TV_WORKER)


async def create_tc_worker_if_not_exist(
        user_scheme_create_tc_worker: UserSchemeRequestCreateTCWorker,
) -> str | None:
    return await create_system_user(user_scheme_create_tc_worker.name, Role.TC_WORKER)


async def create_team(
        user_scheme_create_team: UserSchemeRequestCreateTeam,
) -> UserSchemeResponseCreateTeam:
    async with async_session() as session:
        password = generate_password()
        api_secret = generate_password()
        
        if user_scheme_create_team.economic_model not in (
                EconomicModel.CRYPTO,
                EconomicModel.FIAT,
                EconomicModel.FIAT_CRYPTO_PROFIT,
                EconomicModel.CRYPTO_FIAT_PROFIT,
        ):
            raise exceptions.WrongTypeException()
        
        user_model: UserModel = UserModel(
            wallet_id=user_scheme_create_team.wallet_id,
            namespace=user_scheme_create_team.namespace,
            password_hash=get_password_hash(password),
            name=user_scheme_create_team.name,
            role=Role.TEAM,
            is_enabled=False,
            is_blocked=False,
            is_inbound_enabled=False,
            is_outbound_enabled=True,
            economic_model=user_scheme_create_team.economic_model,
            currency_id=user_scheme_create_team.currency_id,
            credit_factor=user_scheme_create_team.credit_factor,
            trust_balance=0,
            profit_balance=0,
            api_secret=api_secret,
            telegram_bot_secret=user_scheme_create_team.telegram_bot_secret,
            telegram_verifier_chat_id=user_scheme_create_team.telegram_verifier_chat_id,
        )
        session.add(user_model)
        await session.flush()
        user_model.balance_id = user_model.id
        await session.commit()
        
        return UserSchemeResponseCreateTeam(
            wallet_id=user_model.wallet_id,
            namespace=user_model.namespace,
            id=user_model.id,
            name=user_model.name,
            password=password,
            role=user_model.role,
            create_timestamp=datetime.timestamp(user_model.create_timestamp),
            is_enabled=user_model.is_enabled,
            is_blocked=user_model.is_blocked,
            api_secret=api_secret,
            trust_balance=user_model.trust_balance,
            profit_balance=user_model.profit_balance,
        )


async def create_merchant(
        user_scheme_create_merchant: UserSchemeRequestCreateMerchant,
) -> UserSchemeResponseCreateMerchant:
    async with async_session() as session:
        if user_scheme_create_merchant.economic_model not in (
                EconomicModel.CRYPTO,
                EconomicModel.FIAT,
                EconomicModel.FIAT_CRYPTO_PROFIT,
                EconomicModel.CRYPTO_FIAT_PROFIT,
        ):
            raise exceptions.WrongTypeException()
        password = generate_password()
        api_secret = generate_password()
        merchant_model: UserModel = UserModel(
            wallet_id=user_scheme_create_merchant.wallet_id,
            namespace=user_scheme_create_merchant.namespace,
            password_hash=get_password_hash(password),
            name=user_scheme_create_merchant.name,
            role=Role.MERCHANT,
            is_inbound_enabled=False,
            is_outbound_enabled=False,
            economic_model=user_scheme_create_merchant.economic_model,
            currency_id=user_scheme_create_merchant.currency_id,
            credit_factor=user_scheme_create_merchant.credit_factor,
            is_enabled=False,
            is_blocked=False,
            api_secret=api_secret,
            trust_balance=0,
            profit_balance=0,
        )
        session.add(merchant_model)
        await session.flush()
        merchant_model.balance_id = merchant_model.id
        await session.commit()
        return UserSchemeResponseCreateMerchant(
            wallet_id=merchant_model.wallet_id,
            namespace=merchant_model.namespace,
            id=merchant_model.id,
            name=merchant_model.name,
            password=password,
            role=merchant_model.role,
            create_timestamp=datetime.timestamp(merchant_model.create_timestamp),
            is_enabled=merchant_model.is_enabled,
            is_blocked=merchant_model.is_blocked,
            trust_balance=merchant_model.trust_balance,
            profit_balance=merchant_model.profit_balance,
            api_secret=api_secret,
        )


async def create_agent(
        user_scheme_create_agent: UserSchemeRequestCreateAgent,
) -> UserSchemeResponseCreateAgent:
    async with async_session() as session:
        password = generate_password()
        agent_model: UserModel = UserModel(
            wallet_id=user_scheme_create_agent.wallet_id,
            namespace=user_scheme_create_agent.namespace,
            password_hash=get_password_hash(password),
            name=user_scheme_create_agent.name,
            role=Role.AGENT,
            is_enabled=False,
            is_blocked=False,
            is_inbound_enabled=False,
            is_outbound_enabled=False,
            currency_id="system_AGENT",
            trust_balance=0,
            profit_balance=0,
        )
        session.add(agent_model)
        await session.flush()
        agent_model.balance_id = agent_model.id
        await session.commit()
        
        return UserSchemeResponseCreateAgent(
            wallet_id=agent_model.wallet_id,
            namespace=agent_model.namespace,
            id=agent_model.id,
            name=agent_model.name,
            password=password,
            role=agent_model.role,
            create_timestamp=datetime.timestamp(agent_model.create_timestamp),
            is_blocked=agent_model.is_blocked,
            profit_balance=agent_model.profit_balance,
        )


async def create_support(user_scheme_create_support: UserSchemeRequestCreateSupport):
    async with async_session() as session:
        password = generate_password()
        user: UserModel = UserModel(
            namespace=user_scheme_create_support.namespace,
            password_hash=get_password_hash(password),
            name=user_scheme_create_support.name,
            role=Role.SUPPORT,
            is_enabled=False,
            is_blocked=False,
        )
        session.add(user)
        await session.commit()
        
        response = UserSchemeResponseCreateSupport(
            id=user.id,
            namespace=user.namespace,
            name=user.name,
            password=password,
            role=user.role,
            create_timestamp=user.create_timestamp,
            is_blocked=user.is_blocked,
        )
        
        return response


# -----------------------------------------------GET-----------------------------------------------


async def user_get_by_id_(user_id: str, session: AsyncSession) -> UserModel:
    result = await session.execute(
        select(UserModel)
        .options(selectinload(UserModel.user_role).selectinload(RoleModel.permissions).load_only(PermissionModel.code))
        .where(UserModel.id == user_id)
    )
    user = result.scalars().first()
    if user is None:
        raise exceptions.UserNotFoundException()
    return user


async def user_get_by_id(
        user_scheme_request_get_by_id: UserSchemeRequestGetById,
) -> ExpandedUserSchemeResponse:
    async with ro_async_session() as session:
        user = await user_get_by_id_(user_scheme_request_get_by_id.id, session)
        result = ExpandedUserSchemeResponse(**user.__dict__)
        
        return result


async def find_root(session: AsyncSession) -> UserModel:
    result = await session.execute(select(UserModel).where(UserModel.role == Role.ROOT))
    user = result.scalars().first()
    return user


async def user_get_by_password_hash(
        user_scheme_request_get_by_password_hash: UserSchemeRequestGetByPasswordHash,
) -> UserSchemeResponse:
    async with ro_async_session() as session:
        result = await session.execute(
            select(UserModel).where(
                UserModel.password_hash
                == user_scheme_request_get_by_password_hash.password_hash
            )
        )
        user = result.scalars().first()
        if user is None:
            raise exceptions.UserNotFoundException()
    return UserSchemeResponse(**user.__dict__)


async def user_get_by_api_secret(
        request: UserSchemeRequestGetByApiSecret,
) -> UserSchemeResponse:
    async with ro_async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.api_secret == request.api_secret)
        )
        user = result.scalars().first()
        if user is None:
            raise exceptions.UserNotFoundException()
    return UserSchemeResponse(**user.__dict__)


# -----------------------------------------------UPDATE--------------------------------------------
async def get_credit_factor_(user_id: str, session: async_session):
    stmt = union_all(
        select(TeamModel.credit_factor).where(TeamModel.id == user_id),
        select(MerchantModel.credit_factor).where(MerchantModel.id == user_id),
    ).scalar_subquery()

    credit_factor = (await session.execute(select(stmt))).scalars().first()

    if credit_factor is None:
        return 0

    return credit_factor


async def disable_user_by_credit_factor(
        user_id: str, exchange_rate: int, session: AsyncSession
):
    credit_factor: int = await get_credit_factor_(user_id=user_id, session=session)
    balances = await get_balances(
        user_id=user_id,
        session=session,
    )

    print("disable_user_by_credit_factor", credit_factor, balances)

    debt = balances[0] + balances[3] * DECIMALS // exchange_rate
    if debt <= credit_factor * DECIMALS:
        user = await user_get_by_id_(user_id, session=session)
        if user.role == Role.MERCHANT:
            user.is_outbound_enabled = False
        if user.role == Role.TEAM:
            user.is_inbound_enabled = False


async def change_switcher(
        user_id: str,
        value: bool,
        direction: str,
) -> WorkingUser:
    async with async_session() as session:
        user = await v2_user_get_by_id(user_id, session)

        if direction == Direction.INBOUND:
            user.is_inbound_enabled = value
        if direction == Direction.OUTBOUND:
            user.is_outbound_enabled = value

        session.add(user)
        await session.commit()

    return user


# -------------------------------------NEW--------------------------------------------------------

async def v2_user_get_by_id(user_id: str, active_session: Optional[AsyncSession] = None) -> User | None:
    if active_session is None:
        async with ro_async_session() as session:
            user = await session.get(UserModel, user_id)

            return user
    else:
        return await active_session.get(UserModel, user_id)


async def v2_user_get_by_password_hash(password_hash: str) -> User:
    async with ro_async_session() as session:
        user = (await session.execute(
            select(UserModel)
            .where(UserModel.password_hash == password_hash)
        )).scalar_one_or_none()

        if user is None:
            raise exceptions.UserNotFoundException()

        return get_user_scheme(user)

# async def v2_user_get_by_api_secret(api_secret: str) -> User:
#     async with ro_async_session() as session:
#         user = (await session.execute(
#             select(UserModel)
#             .where(UserModel.api_secret == api_secret)
#         )).scalar_one_or_none()

#         if user is None:
#             raise exceptions.UserNotFoundException()

#         return get_user_scheme(user)


async def v2_user_get_merchant_by_api_secret(api_secret: str) -> UserMerchantScheme:
    async with ro_async_session() as session:
        user = (await session.execute(
            select(MerchantModel)
            .where(MerchantModel.api_secret == api_secret)
        )).scalar_one_or_none()

        if user is None:
            raise exceptions.UserNotFoundException()

        return get_user_scheme(user)

# -------------------------------------END NEW--------------------------------------------------------


async def code_create_user():
    for i in range(2, 16):
        r = await create_team(
            UserSchemeRequestCreateTeam(
                name=f"RufTeam #{i}",
                telegram_bot_secret="7084051208:AAGEvxu5b1Y2KX7kMmdXZs16poX_r6wl_o4",
                telegram_verifier_chat_id="-1004133792972",
            )
        )
        print(f"{r.name} {r.id}")
        #print(f"password: `{r.password}`")
        #print(f"android: `{r.api_secret}`")
        print()


async def validate_team_by_api(api_secret: str):
    async with ro_async_session() as session:
        result = await session.execute(
            select(TeamModel.id, TeamModel.name)
            .where(TeamModel.api_secret == api_secret)
        )
        user = result.one_or_none()

        if user is None:
            raise exceptions.UserNotFoundException()

        team_id, team_name = user
        return {"team_id": team_id, "name": team_name}


if __name__ == "__main__":
    # print(generate_password())
    # print(asyncio.run(create_team(
    #     UserSchemeRequestCreateTeam(
    #         name='TEEEEEEEST',
    #         economic_model='fiat_crypto_profit',
    #         currency_id='RUB',
    #             telegram_bot_secret='7084051208:AAGEvxu5b1Y2KX7kMmdXZs16poX_r6wl_o4',
    #             telegram_verifier_chat_id='-1002013323596'
    #     )
    # )))
    # print(asyncio.run(create_team(UserSchemeRequestCreateTeam(
    #     name='1SPIN / URAL / TEAM #3',
    #     telegram_bot_secret='7084051208:AAGEvxu5b1Y2KX7kMmdXZs16poX_r6wl_o4',
    #     telegram_verifier_chat_id='-1002013323596'
    # ))))
    # asyncio.run(code_create_user())
    print(
        asyncio.run(
            create_agent(
                UserSchemeRequestCreateAgent(
                    name="Agent_Myrad_1spin",
                )
            )
        )
    )
