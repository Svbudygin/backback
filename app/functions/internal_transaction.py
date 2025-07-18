import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    func,
    null,
    select,
    true,
    or_,
    and_,
    cast,
    String
)
from app.functions.user import get_credit_factor_
import app.exceptions as exceptions
import app.schemas.InternalTransactionScheme as ITs
from app.schemas.UserScheme import User, WorkingUser, UserSupportScheme
from app.core.constants import Status, Direction, Limit, DECIMALS, Role
from app.core.session import async_session, ro_async_session
from app.functions.balance import get_balances, add_balance_changes, get_balance_id_by_user_id
from app.functions.external_transaction import get_search_filters
from app.functions.crypto import get_amount_by_hash
from app.functions.user import user_get_by_id_
from app.models import WalletModel, UserModel, NamespaceModel, MerchantModel, TeamModel, GeoSettingsModel
from app.models.InternalTransactionModel import InternalTransactionModel


async def internal_transaction_create(
        request_create_open: ITs.InboundRequestCreateOpenDB | ITs.OutboundRequestCreateOpenDB,
        current_user: WorkingUser | None = None,
) -> ITs.Response:
    async with async_session() as session:
        if type(request_create_open) is ITs.InboundRequestCreateOpenDB:
            geo_settings_q = await session.execute(
                select(GeoSettingsModel.block_deposit).where(GeoSettingsModel.id == current_user.geo.id)
            )
            block_deposit = geo_settings_q.scalar()
            if block_deposit == True and current_user.role == Role.TEAM:
                raise exceptions.BlockedDepositFromSupports()
            wallet_q = await session.execute(
                select(WalletModel)
                .filter(
            UserModel.id == request_create_open.user_id,
                    NamespaceModel.id == UserModel.namespace_id,
                    WalletModel.id == NamespaceModel.wallet_id
                )
            )

            wallet = wallet_q.scalars().first()

            if wallet is None:
                raise exceptions.WalletNotFoundException()

            used_amounts_q = await session.execute(
                select(InternalTransactionModel.amount).filter(
            InternalTransactionModel.direction == Direction.INBOUND,
                    InternalTransactionModel.create_timestamp >=
                    func.now() - datetime.timedelta(seconds=Limit.INTERNAL_INBOUND_BACK_TIME_S)
                )
            )
            used_amounts = [i[0] for i in used_amounts_q.all()]
            while request_create_open.amount in used_amounts:
                request_create_open.amount += DECIMALS

            transaction_model: InternalTransactionModel = InternalTransactionModel(
                **request_create_open.__dict__,
                status=Status.PENDING,
                direction=Direction.INBOUND,
                address=wallet.wallet_address,
                from_address=None
            )
            session.add(transaction_model)
        else:
            wallet_q = await session.execute(
                select(WalletModel).filter(
            UserModel.id == request_create_open.user_id,
                    NamespaceModel.id == UserModel.namespace_id,
                    WalletModel.id == NamespaceModel.withdraw_wallet_id
                )
            )
            wallet = wallet_q.scalars().first()

            balances = await get_balances(
                user_id=request_create_open.user_id,
                session=session

            )
            credit_factor = await get_credit_factor_(user_id=request_create_open.user_id, session=session)
            credit_factor = max(credit_factor, 0)
            if balances[0] - credit_factor * DECIMALS < request_create_open.amount:
                raise exceptions.ProfitBalanceNotEnoughException()
            if request_create_open.amount < 0:
                raise exceptions.ProfitBalanceNotEnoughException()

            data = request_create_open.__dict__
            is_autowithdraw_enabled = data.get('is_autowithdraw_enabled')
            del data['is_autowithdraw_enabled']

            transaction_model: InternalTransactionModel = InternalTransactionModel(
                **data,
                status=Status.PENDING,
                direction=Direction.OUTBOUND,
                from_address=wallet.wallet_address if is_autowithdraw_enabled else None
            )
            session.add(transaction_model)
            balance_id = await get_balance_id_by_user_id(user_id=request_create_open.user_id,
                                                         session=session)
            await add_balance_changes(session=session,
                                      changes=[{
                                          'transaction_id': transaction_model.id,
                                          'user_id': request_create_open.user_id,
                                          'balance_id': balance_id,
                                          'trust_balance': -request_create_open.amount,
                                      }])

        await session.commit()
        # balances = await get_balances(
        #     user_id=request_create_open.user_id,
        #     session=session
        # )
        await session.commit()

        await session.refresh(transaction_model)

        return ITs.Response(
            **transaction_model.__dict__,
        )


async def internal_transaction_list(
        request_list: ITs.RequestList,
        namespace_id: int | None = None,
        user_id: str | None = None
) -> ITs.ResponseList:
    queries = get_search_filters(request_list)
    async with ro_async_session() as session:
        if request_list.role == Role.SUPPORT:
            trx_list = await session.execute(
                select(
                    InternalTransactionModel,
                    UserModel.name.label("user_name"),
                    TeamModel.geo_id.label("team_geo_id"),
                    MerchantModel.geo_id.label("merchant_geo_id")
                ).distinct()
                .outerjoin(
                    MerchantModel,
                    cast(InternalTransactionModel.user_id, String) == cast(MerchantModel.id, String)
                )
                .outerjoin(
                    TeamModel,
                    cast(InternalTransactionModel.user_id, String) == cast(TeamModel.id, String)
                )
                .outerjoin(
                    UserModel,
                    InternalTransactionModel.user_id == UserModel.id
                )
                .filter(
                    UserModel.role == request_list.search_role if request_list.search_role is not None else true(),
                    InternalTransactionModel.user_id == request_list.user_id if request_list.user_id is not user_id else true(),
                    UserModel.namespace_id == namespace_id if request_list.role == Role.SUPPORT else true(),
                    InternalTransactionModel.offset_id < request_list.last_offset_id,
                    or_(
                        and_(
                            UserModel.role == "team",
                            TeamModel.geo_id == request_list.geo_id if request_list.geo_id is not None else true(),
                        ),
                        and_(
                            UserModel.role == "merchant",
                            MerchantModel.geo_id == request_list.geo_id if request_list.geo_id is not None else true(),
                        ),
                        UserModel.role.not_in(["team", "merchant"])
                    ),
                    *queries
                )
                .order_by(InternalTransactionModel.offset_id.desc())
                .limit(request_list.limit)
            )

            return ITs.ResponseList(
                items=[
                    ITs.Response(
                        **i[0].__dict__,
                        user_name=i[1]
                    )
                    for i in trx_list
                ]
            )
        else:
            trx_list = await session.execute(
                select(InternalTransactionModel).filter(
                    InternalTransactionModel.user_id == request_list.user_id,
                ).filter(
                    InternalTransactionModel.offset_id < request_list.last_offset_id,
                    *queries
                )
                .order_by(
                    InternalTransactionModel.offset_id.desc())
                .limit(request_list.limit))
            result = trx_list.scalars().fetchall()
            return ITs.ResponseList(
                items=[ITs.Response(
                    **i.__dict__,
                )
                    for i in result])


async def internal_transaction_get_pending(
        request_list: ITs.RequestList
) -> ITs.ResponseList:
    async with ro_async_session() as session:
        trx_list = await session.execute(
            select(InternalTransactionModel).filter(
                InternalTransactionModel.offset_id < request_list.last_offset_id,
                InternalTransactionModel.status == Status.PENDING
            )
            .order_by(
                InternalTransactionModel.offset_id.desc())
            .limit(request_list.limit))
        result = trx_list.scalars().fetchall()
        return ITs.ResponseList(
            items=[ITs.Response(**i.__dict__)
                   for i in result])


async def _find_internal_transaction_by_id(
        transaction_id: str, session: AsyncSession) -> InternalTransactionModel:
    contract_req = await session.execute(
        select(InternalTransactionModel).filter(
            InternalTransactionModel.id == transaction_id).with_for_update())
    result = contract_req.scalars().first()
    if result is None:
        raise exceptions.InternalTransactionNotFoundException
    return result


async def internal_transaction_support_update(
        update_status_db: ITs.RequestUpdateStatusDB
) -> ITs.Response:
    async with async_session() as session:
        transaction_model: InternalTransactionModel = await _find_internal_transaction_by_id(
            update_status_db.id,
            session
        )
        if update_status_db.status == Status.CLOSE and transaction_model.status == Status.ACCEPT:
            raise exceptions.InternalTransactionRequestStatusException(
                statuses=[Status.ACCEPT]
            )

        result = await session.execute(
            select(InternalTransactionModel).filter_by(blockchain_transaction_hash=update_status_db.hash)
        )

        existing_entry = result.scalars().first()

        if existing_entry and update_status_db.hash is not None:
            raise exceptions.ExistingHashException()

        if update_status_db.hash is not None:
            real_amount = await get_amount_by_hash(update_status_db.hash)
        else:
            real_amount = transaction_model.amount

        if transaction_model.direction == Direction.INBOUND:
            if ((transaction_model.status == Status.CLOSE or transaction_model.status == Status.PENDING)
                    and update_status_db.status == Status.ACCEPT):
                transaction_model.blockchain_transaction_hash = update_status_db.hash
                transaction_model.amount = real_amount
                balance_id = await get_balance_id_by_user_id(user_id=transaction_model.user_id,
                                                             session=session)
                await add_balance_changes(
                    session=session,
                    changes=[{
                        'balance_id': balance_id,
                        'transaction_id': transaction_model.id,
                        'user_id': transaction_model.user_id,
                        'trust_balance': real_amount
                    }])
                transaction_model.status = update_status_db.status
            else:
                raise exceptions.InternalTransactionRequestStatusException(
                    statuses=[Status.ACCEPT]
                )

        if transaction_model.direction == Direction.OUTBOUND:
            if ((transaction_model.status == Status.PROCESSING or transaction_model.status == Status.PENDING)
                    and update_status_db.status == Status.ACCEPT):
                transaction_model.blockchain_transaction_hash = update_status_db.hash
                transaction_model.status = update_status_db.status
                balance_id = await get_balance_id_by_user_id(user_id=transaction_model.user_id,
                                                             session=session)
                user = await session.get(UserModel, transaction_model.user_id)
                trust_balance = -(real_amount - transaction_model.amount)
                #if user.role != Role.MERCHANT:
                #    trust_balance -= 5 * DECIMALS
                await add_balance_changes(
                    session=session,
                    changes=[{
                        'balance_id': balance_id,
                        'transaction_id': transaction_model.id,
                        'user_id': transaction_model.user_id,
                        'trust_balance': trust_balance
                    }])
                transaction_model.amount = real_amount

            if ((transaction_model.status == Status.PROCESSING or transaction_model.status == Status.PENDING)
                    and update_status_db.status == Status.CLOSE and update_status_db.hash == None):
                balance_id = await get_balance_id_by_user_id(user_id=transaction_model.user_id,
                                                             session=session)
                await add_balance_changes(
                    session=session,
                    changes=[{
                        'balance_id': balance_id,
                        'transaction_id': transaction_model.id,
                        'user_id': transaction_model.user_id,
                        'trust_balance': transaction_model.amount
                    }])
                transaction_model.status = update_status_db.status
                transaction_model.blockchain_transaction_hash = null()

        if transaction_model.status == Status.ACCEPT and transaction_model.direction == Direction.INBOUND:
            balances = await get_balances(
                user_id=transaction_model.user_id,
                session=session
            )
            if balances[0] + transaction_model.amount >= 0:
                user = await user_get_by_id_(
                    user_id=transaction_model.user_id,
                    session=session)
                # user.is_enabled = True
                print('auto enabling user')

        await session.commit()
        # balances = await get_balances(
        #     user_id=transaction_model.user_id,
        #     session=session
        # )
        await session.commit()
        user = await user_get_by_id_(
            user_id=transaction_model.user_id,
            session=session)
        return ITs.Response(
            **transaction_model.__dict__, user_name=user.name
        )


async def internal_transaction_update(
        update_status_db: ITs.RequestUpdateStatusDB
) -> ITs.Response:
    async with async_session() as session:
        transaction_model: InternalTransactionModel = await _find_internal_transaction_by_id(
            update_status_db.id,
            session
        )

        if update_status_db.hash != None:
            result = await session.execute(
                select(InternalTransactionModel).filter_by(blockchain_transaction_hash=update_status_db.hash)
            )
            existing_entry = result.scalars().first()
            if existing_entry:
                raise exceptions.ExistingHashException()
            transaction_model.blockchain_transaction_hash = update_status_db.hash

        if transaction_model.status == Status.PROCESSING and update_status_db.status == Status.PROCESSING:
            raise exceptions.InternalTransactionStatusProcessingException()

        if (transaction_model.status != Status.ACCEPT
                and update_status_db.status == Status.ACCEPT):
            if transaction_model.direction == Direction.INBOUND:
                balance_id = await get_balance_id_by_user_id(user_id=transaction_model.user_id,
                                                             session=session)
                await add_balance_changes(
                    session=session,
                    changes=[{
                        'balance_id': balance_id,
                        'transaction_id': transaction_model.id,
                        'user_id': transaction_model.user_id,
                        'trust_balance': transaction_model.amount
                    }])

        if (transaction_model.status != Status.CLOSE and update_status_db.status == Status.CLOSE
                and transaction_model.direction == Direction.OUTBOUND):
            balance_id = await get_balance_id_by_user_id(user_id=transaction_model.user_id,
                                                         session=session)
            await add_balance_changes(
                session=session,
                changes=[{
                    'balance_id': balance_id,
                    'transaction_id': transaction_model.id,
                    'user_id': transaction_model.user_id,
                    'trust_balance': transaction_model.amount
                }])

        transaction_model.status = update_status_db.status
        if transaction_model.status == Status.ACCEPT and transaction_model.direction == Direction.INBOUND:
            balances = await get_balances(
                user_id=transaction_model.user_id,
                session=session
            )
            if balances[0] + transaction_model.amount >= 0:
                user = await user_get_by_id_(
                    user_id=transaction_model.user_id,
                    session=session)
                # user.is_enabled = True
                print('auto enabling user')
        
        await session.commit()
        # balances = await get_balances(
        #     user_id=transaction_model.user_id,
        #     session=session
        # )
        await session.commit()
        user = await user_get_by_id_(
            user_id=transaction_model.user_id,
            session=session)
        return ITs.Response(
            **transaction_model.__dict__, user_name=user.name
        )
