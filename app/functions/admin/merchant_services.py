from typing import Dict, List, Tuple
from app.models import UserModel, MerchantModel, FeeContractModel, TrafficWeightContractModel
from app.core.security import generate_password, get_password_hash
from app.repositories.admin.merchant_repo import MerchantRepo
from app.schemas.admin.MerchantScheme import MerchantResponseScheme, V2MerchantResponseScheme
from app.functions.balance import add_balance_changes, get_balances
from app.functions.admin.base_services import (
    validate_unique_user,
    validate_user_has_role,
)
from app.core.constants import Role
from app.utils.session import get_session, async_session
from app.core.session import ro_async_session
from sqlalchemy import select, update


async def create_merch_user(
        session,
        name: str,
        namespace_id: int,
        currency_id: str,
        credit_factor: int,
        geo_id: int,
        balance_id: str | None
) -> Tuple[UserModel, Dict]:
    async with get_session(session) as session:
        password = generate_password()
        api_secret = generate_password()

        merchant_model = MerchantModel(
            password_hash=get_password_hash(password),
            name=name,
            role=Role.MERCHANT,
            is_blocked=False,
            namespace_id=namespace_id,
            credit_factor=credit_factor,
            api_secret=api_secret,
            is_inbound_enabled=False,
            is_outbound_enabled=False,
            currency_id=currency_id,
            geo_id=geo_id
        )

        session.add(merchant_model)
        await session.flush()

        merchant_model.balance_id = merchant_model.id if balance_id is None else balance_id
        return merchant_model, {"password": password, "api_secret": api_secret}


async def create_and_get_merch_user(
        name: str,
        namespace_id: int,
        currency_id: str,
        credit_factor: int,
        geo_id: int,
        balance_id: str | None
):
    async with get_session() as session:
        async with session.begin():
            await validate_unique_user(
                session,
                name=name,
                namespace_id=namespace_id
            )

            user, credentials = await create_merch_user(
                session,
                name=name,
                namespace_id=namespace_id,
                currency_id=currency_id,
                credit_factor=credit_factor,
                geo_id=geo_id,
                balance_id=balance_id
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

            merch_user: V2MerchantResponseScheme = await MerchantRepo.get(
                session,
                merch_id=user.id
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

            merch_user = merch_user.model_copy(update=update)

            await session.commit()

            return merch_user


async def list_merchant_users(
    geo_id: int | None,
    namespace_id: int,
    session=None,
) -> List[V2MerchantResponseScheme]:
    async with ro_async_session() as session:
        users: List[V2MerchantResponseScheme] = await MerchantRepo.list(
            session=session,
            geo_id=geo_id,
            namespace_id=namespace_id
        )
        return users


async def update_merchant_user(session=None, **kwargs) -> V2MerchantResponseScheme:
    async with get_session(session) as session:
        await validate_user_has_role(
            session=session,
            user_id=kwargs["user_id"],
            role=kwargs["role"]
        )

        if kwargs.get("is_blocked") is True:
            upd_query1 = (
                update(FeeContractModel)
                .where(
                    FeeContractModel.merchant_id == kwargs["user_id"],
                    FeeContractModel.is_deleted == False
                )
                .values(is_deleted=True)
            )
            await session.execute(upd_query1)
            upd_query2 = (
                update(TrafficWeightContractModel)
                .where(
                    TrafficWeightContractModel.merchant_id == kwargs["user_id"],
                    TrafficWeightContractModel.is_deleted == False
                )
                .values(is_deleted=True)
            )
            await session.execute(upd_query2)

        user = await MerchantRepo.update(session=session, **kwargs)
        await session.commit()
        return user


async def regenerate_merchant_user(merchant_id: str) -> V2MerchantResponseScheme:
    async with async_session() as session:
            merchant_user: MerchantResponseScheme = await MerchantRepo.get(session, merch_id=merchant_id)
            model_user = await session.execute(select(UserModel).where(UserModel.id == merchant_id))
            model_user = model_user.scalar_one()
            model_merchant = await session.execute(select(MerchantModel).where(MerchantModel.id == merchant_id))
            model_merchant = model_merchant.scalar_one()
            password = generate_password()
            hash = get_password_hash(password)
            api_secret = generate_password()
            credentials = {
                "password_hash": hash,
                "api_secret": api_secret
            }
            model_user.password_hash = hash
            model_merchant.api_secret = api_secret
            await session.flush()
            update = {
                **credentials,
                "password": password
            }
            updated_merchant_user = merchant_user.model_copy(update=update)
            await session.commit()
            return updated_merchant_user
