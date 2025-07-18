import re

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache

import app.exceptions as exceptions
import app.functions.internal_transaction as i_t_f
import app.schemas.InternalTransactionScheme as ITs
from app.schemas.UserScheme import User, WorkingUser, UserSupportScheme
from app.api.deps import (
    v2_get_current_user,
    v2_get_current_working_user,
    v2_get_current_support_user_with_permissions
)
from app.core.constants import Role, Limit, CACHE_TIMEOUT_SMALL_S
from app.models import UserModel, InternalTransactionModel
from sqlalchemy import select
from app.core.session import async_session
from app.enums import Permission

router = APIRouter()


@router.post("/create-inbound")
async def create_internal_transaction_inbound_route(
        create_scheme: ITs.InboundRequestCreateOpen,
        current_user: WorkingUser = Depends(v2_get_current_working_user),
) -> ITs.Response:
    """Create new inbound internal transaction. Available for user with role \"team\" or \"merchant\"."""
    result = await (
        i_t_f.internal_transaction_create(
            ITs.InboundRequestCreateOpenDB(
                **create_scheme.__dict__,
                user_id=current_user.id
            ), current_user))

    return result


@router.post("/create-outbound")
async def create_internal_transaction_inbound_route(
        create_scheme: ITs.OutboundRequestCreateOpen,
        current_user: User = Depends(v2_get_current_user),
) -> ITs.Response:
    """Create new outbound internal transaction. Available for user with role \"team\" or \"merchant\"."""
    if not re.match('^T[A-Za-z0-9]{33}$', create_scheme.address):
        raise exceptions.WrongTRC20AddressFormatException()
    
    if current_user.role not in (Role.TEAM, Role.ROOT, Role.MERCHANT, Role.AGENT):
        raise exceptions.UserWrongRoleException(roles=[Role.TEAM, Role.ROOT, Role.MERCHANT, Role.AGENT])
    
    if create_scheme.amount < Limit.MIN_INTERNAL_OUTBOUND_AMOUNT:
        raise exceptions.WithdrawMinLimitException()
    
    result = await (
        i_t_f.internal_transaction_create(
            ITs.OutboundRequestCreateOpenDB(
                **create_scheme.__dict__,
                user_id=current_user.id,
                is_autowithdraw_enabled=current_user.is_autowithdraw_enabled
            )))

    return result


@router.get("/list")
# @cache(expire=CACHE_TIMEOUT_SMALL_S)
async def list_transaction_route(
        last_offset_id: int,
        limit: int,
        search: str | None = None,
        geo_id: int | None = None,
        role: str | None = None,
        direction: str | None = None,
        status: str | None = None,
        amount_from: int | None = None,
        amount_to: int | None = None,
        create_timestamp_from: int | None = None,
        create_timestamp_to: int | None = None,
        user_id: str | None = None,
        current_user: User = Depends(v2_get_current_user),
) -> ITs.ResponseList:
    """List internal transactions. Using pagination: Items with id LESS than <b>last_offset_id</b>. Items amount is
    <b>limit</b> or less if it is end. Available for user with role \"merchant\" or "\team\"."""
    
    transaction_params = ITs.RequestList(
        limit=limit,
        last_offset_id=last_offset_id,
        user_id=user_id if user_id is not None else current_user.id,
        role=current_user.role,
        search_role=role,
        search=search,
        geo_id=geo_id if search is None else None,
        direction=direction,
        status=status,
        amount_from=amount_from,
        amount_to=amount_to,
        create_timestamp_to=create_timestamp_to,
        create_timestamp_from=create_timestamp_from,
    )
    
    if transaction_params.user_id != current_user.id and current_user.role != Role.ROOT:
        if current_user.role != Role.SUPPORT:
            raise exceptions.UserWrongRoleException(roles=[Role.ROOT, Role.SUPPORT])
    if transaction_params.limit > Limit.MAX_ITEMS_PER_QUERY:
        raise exceptions.ListResponseLengthLimitException()
    
    result = await i_t_f.internal_transaction_list(
        ITs.RequestList(**transaction_params.__dict__),
        namespace_id=current_user.namespace.id,
        user_id=current_user.id
    )
    
    return result


@router.put("/update")
async def update_transaction_route(
        update_scheme: ITs.RequestUpdateStatus,
        current_user: User = Depends(v2_get_current_user),
) -> ITs.Response:
    """Update internal transaction details. Available for user with all roles. or """
    
    if current_user.role != Role.C_WORKER:
        raise exceptions.UserWrongRoleException(roles=[Role.C_WORKER])

    result = await i_t_f.internal_transaction_update(
        ITs.RequestUpdateStatusDB(
            **update_scheme.__dict__,
            user_id=current_user.id
        ))

    return result


@router.put("/support/update")
async def update_transaction_route(
        update_scheme: ITs.RequestUpdateStatus,
        current_user: UserSupportScheme = Depends(
            v2_get_current_support_user_with_permissions([Permission.VIEW_WALLET])
        )
) -> ITs.Response:
    """Update transaction details. Available for user with role \"Support\"."""
    async with async_session() as session:
        transaction_namespace_stmt = await session.execute(
            select(
                UserModel.namespace_id
            ).join(
                InternalTransactionModel,
                InternalTransactionModel.user_id == UserModel.id
            ).where(
                InternalTransactionModel.id == update_scheme.id
            )
        )

        transaction_namespace_id = transaction_namespace_stmt.scalar_one_or_none()

        if transaction_namespace_id is None:
            raise exceptions.InternalTransactionNotFoundException()

        if current_user.namespace.id != transaction_namespace_id:
            raise exceptions.InternalTransactionNotFoundException()

    if update_scheme.hash == "":
        update_scheme.hash = None

    result = await i_t_f.internal_transaction_support_update(
        ITs.RequestUpdateStatusDB(
            **update_scheme.__dict__,
            user_id=current_user.id
        )
    )

    return result


@router.get("/pending")
async def get_pending_transactions_route(
        last_offset_id: int,
        limit: int,
        current_user: User = Depends(v2_get_current_user),
):
    transaction_params = ITs.RequestList(
        limit=limit,
        last_offset_id=last_offset_id,
        user_id=current_user.id,
        role=current_user.role,
        search=None,
        direction=None,
        status=None,
        amount_from=None,
        amount_to=None,
        create_timestamp_to=None,
        create_timestamp_from=None
    )
    
    if current_user.role != Role.C_WORKER:
        raise exceptions.UserWrongRoleException(roles=[Role.C_WORKER])
    
    result = await i_t_f.internal_transaction_get_pending(
        ITs.RequestList(**transaction_params.__dict__))
    return result
