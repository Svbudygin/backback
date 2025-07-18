import json
from typing import List

from fastapi import APIRouter, Depends, UploadFile, Request as FastAPIRequest, Response as FastAPIResponse
from fastapi.responses import Response, StreamingResponse, JSONResponse
from starlette.requests import Request

import app.exceptions as exceptions
import app.functions.external_transaction as e_t_f
import app.schemas.ExternalTransactionScheme as ETs
import app.schemas.UserScheme as Us
from app.schemas.WhitelistScheme import WhiteListPayerAddRequest
from app.schemas.UserScheme import (
    User,
    WorkingUser,
    UserTeamScheme,
    UserMerchantScheme,
    UserSupportScheme
)
import app.schemas.v2.ExternalTransactionScheme as v2_ETs
from app.api import deps
from app.api.deps import (
    v2_get_current_user,
    v2_get_current_working_user,
    v2_get_current_team_user,
    v2_get_current_merchant_user,
    v2_get_current_support_user_with_permissions,
    v2_get_current_support_user,
    get_current_user_any_role
)
from app.core.session import async_session
from app.core.constants import Limit, Role, Status, Type, get_class_fields, ReasonName, translations_reason, Direction
from app.core.file_storage import download_file
from app.enums import Permission, TransactionFinalStatusEnum
from app.models import UserModel, ExternalTransactionModel
from sqlalchemy import select

router = APIRouter()

@router.patch(path="/whitelist/", description='''Add payer_id in whitelist. Ask to Support.''')
async def add_to_whitelist(
        request: WhiteListPayerAddRequest,
        current_user: UserMerchantScheme = Depends(v2_get_current_merchant_user)
):
    return await e_t_f.add_whitelist(request, current_user.id)


@router.post(path="/create-inbound")
async def create_inbound_route(
        request: FastAPIRequest,
        create: v2_ETs.H2HCreateInboundJWT,
        current_user: UserMerchantScheme = Depends(v2_get_current_merchant_user),
):
    if not current_user.is_inbound_enabled:
        raise exceptions.UserNotEnabledException()
    
    if create.type and create.type not in get_class_fields(Type):
        raise exceptions.WrongTypeException()
    
    if create.amount < 0 or create.amount > Limit.MAX_INT:
        raise exceptions.WrongTransactionAmountException()

    return await e_t_f.h2h_create_inbound(
        v2_ETs.H2HCreateInbound(
            **create.__dict__,
            currency_id=current_user.currency_id,
            merchant_id=current_user.id,
        ),
        request
    )


@router.post(path="/create-outbound")
async def create_outbound_route(
        create: v2_ETs.H2HCreateOutboundJWT,
        current_user: UserMerchantScheme = Depends(v2_get_current_merchant_user),
):
    if not current_user.is_outbound_enabled:
        raise exceptions.UserNotEnabledException()
    
    if create.type and create.type not in get_class_fields(Type):
        raise exceptions.WrongTypeException()
    
    if create.amount < 0 or create.amount > Limit.MAX_INT:
        raise exceptions.WrongTransactionAmountException()
    
    result = await e_t_f.h2h_create_outbound(
        v2_ETs.H2HCreateOutbound(
            **create.__dict__,
            currency_id=current_user.currency_id,
            merchant_id=current_user.id,
        )
    )
    return result


@router.get("/get-outbound-filters")
async def get_outbound_filters(
        current_user: UserTeamScheme = Depends(v2_get_current_team_user),
):
    return await e_t_f.get_outbound_filters(current_user)


@router.post("/get-outbound")
async def get_outbound(
        get_outbound_request: v2_ETs.GetOutboundRequest,
        request: Request,
        current_user: UserTeamScheme = Depends(v2_get_current_team_user),
) -> ETs.Response:
    result = await e_t_f.get_outbound(
        v2_ETs.GetOutboundRequestDB(
            **get_outbound_request.__dict__, team_id=current_user.id
        ), current_user
    )
    
    # await FastAPICache.clear(namespace=
    #                          (request.headers.get('authorization').replace(' ', '') +
    #                           '/external-transaction/list')
    #                          )
    return result


@router.post(path="/hold")
async def hold_external_transaction(
        id: str,
        current_user: UserTeamScheme = Depends(v2_get_current_team_user),
):
    result = await e_t_f.hold_external_transaction(id, current_user)
    return result



@router.get(path="/get/")
async def get_external_transactions(
        id: str | None = None,
        merchant_transaction_id: str | None = None,
        current_user: User = Depends(v2_get_current_user),
):
    if current_user.role not in [Role.TG_APPEAL_WORKER, Role.MERCHANT]:
        return exceptions.UserWrongRoleException(roles=[Role.MERCHANT])
    return await e_t_f.h2h_get_transaction_info(
        v2_ETs.H2HGetRequest(
            merchant_id=current_user.id if current_user.role == Role.MERCHANT else None,
            id=id,
            merchant_transaction_id=merchant_transaction_id,
        )
    )


def request_key_builder(
        func,
        namespace: str = "",
        request: Request = None,
        response: Response = None,
        *args,
        **kwargs,
):
    return ":".join(
        [
            ":"
            + request.headers.get("authorization").replace(" ", "")
            + request.url.path,
            repr(sorted(request.query_params.items())),
        ]
    )


@router.get("/list")
# @cache(expire=CACHE_TIMEOUT_SMALL_S,
#        key_builder=request_key_builder)
async def list_transaction_route(
        last_priority: int,
        limit: int,
        search: str | None = None,
        geo_id: int | None = None,
        direction: str | None = None,
        status: str | None = None,
        amount_from: int | None = None,
        amount_to: int | None = None,
        currency_id: str | None = None,
        type: str | None = None,
        bank: str | None = None,
        create_timestamp_from: int | None = None,
        create_timestamp_to: int | None = None,
        user_id: str | None = None,
        merchant_id: str | None = None,
        team_id: str | None = None,
        final_status: TransactionFinalStatusEnum | None = None,
        current_user: User = Depends(v2_get_current_user),
) -> ETs.ResponseList:
    """List external transactions. Using pagination: Items with id LESS than <b>last_priority</b>. Items amount is
    <b>limit</b> or less if it is end. Available for user with role \"merchant\" or "\team\".
    """
    transaction_params = ETs.RequestList(
        limit=limit,
        last_priority=last_priority,
        user_id=user_id if user_id is not None else current_user.id,
        role=current_user.role,
        search=search,
        geo_id=geo_id if search is None or current_user.role != Role.SUPPORT else None,
        direction=direction,
        status=status,
        amount_from=amount_from,
        amount_to=amount_to,
        currency_id=currency_id,
        create_timestamp_from=create_timestamp_from,
        create_timestamp_to=create_timestamp_to,
        type=type,
        bank=bank,
        merchant_id=merchant_id if current_user.role == Role.SUPPORT else None,
        team_id=team_id if current_user.role == Role.SUPPORT else None,
        final_status=final_status
    )
    
    if (
            transaction_params.user_id != current_user.id
            and current_user.role != Role.ROOT
    ):
        if current_user.role != Role.SUPPORT:
            raise exceptions.UserWrongRoleException(roles=[Role.ROOT, Role.SUPPORT])
    
    if transaction_params.limit > Limit.MAX_ITEMS_PER_QUERY:
        raise exceptions.ListResponseLengthLimitException()
    
    result = await e_t_f.external_transaction_list(
        ETs.RequestList(**transaction_params.__dict__), namespace_id=current_user.namespace.id
    )

    if current_user.role != Role.SUPPORT:
        geo_name = current_user.geo.name
    else:
        geo_name = "support"
    
    for i in result.items:
        if i.status == Status.OPEN:
            i.status = Status.PENDING
        if i.reason:
            i.reason = translations_reason.get(geo_name, translations_reason["RUB"]).get(
                i.reason, i.reason
            )
    return result


# TODO: current_user = Depends(deps.permissions_required([Permission.TEST]))
@router.put("/update")
async def update_transaction_route(
        update_scheme: ETs.RequestUpdateStatus,
        current_user: WorkingUser = Depends(v2_get_current_working_user),
) -> ETs.Response:
    """Update transaction details. Available for user with role \"Team, Merchant for status close\"."""
    if current_user.role == Role.MERCHANT and update_scheme.status == Status.CLOSE:
        update_data = update_scheme.__dict__.copy()
        update_data["final_status"] = TransactionFinalStatusEnum.CANCEL
        
        return (await e_t_f.external_transaction_update(
            ETs.RequestUpdateStatusDB(**update_data)
        ))

    if current_user.role == Role.TEAM and update_scheme.status == Status.CLOSE:
        raise exceptions.WrongStatusException(statuses=[Status.ACCEPT])

    result = await e_t_f.external_transaction_update(
        ETs.RequestUpdateStatusDB(**update_scheme.__dict__, team_id=current_user.id)
    )

    res = await e_t_f.get_fields_for_update_response(
        result, Role.TEAM
    )
    
    return res


@router.put("/support/update")
async def update_transaction_route(
        update_scheme: ETs.RequestUpdateStatus,
        current_user: UserSupportScheme = Depends(
            v2_get_current_support_user_with_permissions([
                Permission.VIEW_PAY_OUT,
                Permission.VIEW_PAY_IN
            ])
        ),
) -> ETs.Response:
    """Update transaction details. Available for user with role \"Support\"."""
    return await update_transaction_support(update_scheme, current_user)

@router.put("/support/update/search")
async def update_transaction_route_search(
        update_scheme: ETs.RequestUpdateStatus,
        current_user: UserSupportScheme = Depends(
            v2_get_current_support_user_with_permissions([
                Permission.VIEW_SEARCH
            ])
        ),
) -> ETs.Response:
    """Update transaction details. Available for user with role \"Support\" with VIEW_SEARCH permission."""
    return await update_transaction_support(update_scheme, current_user)

async def update_transaction_support(update_scheme: ETs.RequestUpdateStatus,
                             current_user: UserSupportScheme) -> ETs.Response:
    async with async_session() as session:
        transaction_data_stmt = await session.execute(
            select(
                UserModel.namespace_id,
                ExternalTransactionModel.direction
            ).join(
                ExternalTransactionModel,
                ExternalTransactionModel.merchant_id == UserModel.id
            ).where(
                ExternalTransactionModel.id == update_scheme.transaction_id
            )
        )

        row = transaction_data_stmt.one_or_none()
        if row is None:
            raise exceptions.ExternalTransactionNotFoundException()

        transaction_namespace_id, direction = row

        if current_user.namespace.id != transaction_namespace_id:
            raise exceptions.ExternalTransactionNotFoundException()

        if direction == Direction.INBOUND and update_scheme.status == Status.CLOSE:
            raise exceptions.WrongStatusException(statuses=[Status.ACCEPT])

    result = await e_t_f.external_transaction_update(
        ETs.RequestUpdateStatusDB(**update_scheme.__dict__)
    )

    res = await e_t_f.get_fields_for_update_response(
        result, Role.SUPPORT
    )

    return res

@router.put("/transfer")
async def update_transaction_route(
        request: Request,
        update_scheme: ETs.RequestTransfer,
        current_user: UserTeamScheme = Depends(v2_get_current_team_user),
) -> ETs.Response:
    """Update transaction details. Available for user with role \"Team\"."""
    result = await e_t_f.external_transaction_transfer(
        team_id=current_user.id,
        transaction_id=update_scheme.transaction_id
    )
    # await FastAPICache.clear(namespace=
    #                          (request.headers.get('authorization').replace(' ', '') +
    #                           '/external-transaction/list')
    #                          )
    return result


@router.post("/{transaction_id}/transfer-to-team")
async def transfer_to_team(
    transaction_id: str,
    data: ETs.RequestTransferToTeam,
    _: UserSupportScheme = Depends(v2_get_current_support_user)
):
    return await e_t_f.transfer_pay_out_to_team(transaction_id, data)


@router.post("/{transaction_id}/back-to-pool")
async def back_to_pool(
    transaction_id: str,
    _: UserSupportScheme = Depends(v2_get_current_support_user)
):
    return await e_t_f.return_transaction_to_pool(transaction_id)


@router.put("/update-from-verifier")
async def update_transaction_from_verifier_route(
        update_scheme: ETs.RequestUpdateStatusDB,
        current_user: User = Depends(v2_get_current_user),
):
    """Update transaction details. Available for user with role \"Verifier\"."""
    if current_user.role != Role.TV_WORKER:
        raise exceptions.UserWrongRoleException(roles=[Role.TV_WORKER])

    if update_scheme.status == Status.CLOSE:
        return JSONResponse(content={"detail": "Nothing"}, status_code=200)
    
    update_data = update_scheme.__dict__.copy()
    update_data["final_status"] = TransactionFinalStatusEnum.AUTO

    result = await e_t_f.external_transaction_update(
        ETs.RequestUpdateStatusDB(**update_data)
    )

    return result


@router.get("/reasons")
async def get_reasons_route(
    current_user: User = Depends(v2_get_current_user)
):
    if current_user.role != Role.SUPPORT:
        geo_name = current_user.geo.name
    else:
        geo_name = "support"

    reasons = []

    for reason in ReasonName:
        reason_key = reason.value
        localized = translations_reason.get(geo_name, translations_reason["RUB"]).get(reason_key, reason_key)
        reasons.append({"code": reason_key, "title": localized})

    return reasons


@router.put("/update-with-reason")
async def decline_with_reason(
        request: ETs.DeclineRequest,
        current_user: UserTeamScheme = Depends(v2_get_current_team_user),
) -> ETs.Response:
    status = Status.CLOSE
    result = await e_t_f.external_transaction_update(
        ETs.RequestUpdateStatusDB(transaction_id=request.transaction_id, reason=request.reason, status=status, team_id=current_user.id)
    )

    await e_t_f.external_transaction_update_file_reason(
        request.transaction_id, request.files, current_user
    )

    res = await e_t_f.get_fields_for_update_response(
        result, Role.TEAM
    )

    geo_name = current_user.geo.name

    if res.reason:
        res.reason = translations_reason.get(geo_name, translations_reason["RUB"]).get(
            res.reason, res.reason
        )

    return res


@router.put("/update-file")
async def update_transaction_file_route(
        files: List[UploadFile],
        transaction_id: str,
        current_user: User = Depends(get_current_user_any_role([Role.TEAM, Role.SUPPORT]))
) -> ETs.Response:
    """Update file. Available for user with role \"Team\"."""
    update_file_scheme = ETs.RequestUpdateStatus(
        transaction_id=transaction_id,
        status=Status.PENDING
    )

    result = await e_t_f.external_transaction_update_file_and_send_to_tg(
        request_update_file=ETs.RequestUpdateFileDB(
            **update_file_scheme.__dict__,
            team_id=current_user.id,
            file_uri="https://file-updated",
        ),
        current_user=current_user,
        files=files,
    )
    
    return result


@router.get("/download-file/{file_id}")
async def download_file_route(
        file_id: str,
        _: User = Depends(v2_get_current_user)
) -> StreamingResponse:
    return StreamingResponse(
        download_file(file_id), media_type="application/octet-stream"
    )


@router.put("/accept-from-device")
async def update_transaction_file_route(
        update_from_device: ETs.RequestUpdateFromDevice,
        request: Request,
) -> ETs.Response | None:
    data = json.loads(await request.body())
    data.pop('api_secret', None)
    print('__update_transaction_file_route', data)
    if len(update_from_device.message.title) > Limit.MAX_STRING_LENGTH_SMALL:
        raise exceptions.TitleResponseLengthLimitException()

    result = await e_t_f.external_transaction_update_from_device(
        ETs.RequestUpdateFromDeviceDB(
            bank=update_from_device.message.title,
            package_name=update_from_device.message.package_name,
            message=update_from_device.message.extra_text,
            device_hash=update_from_device.device_hash,
            api_secret=update_from_device.api_secret,
            timestamp=(
                update_from_device.message.timestamp // 1000
                if update_from_device.message.timestamp is not None
                else None
            ),
        )
    )
    return result


@router.get("/categories")
async def get_categories(current_user: User = Depends(v2_get_current_user)):
    return await e_t_f.get_categories(current_user)

@router.get("/final-statuses")
def get_final_statuses(current_user: User = Depends(v2_get_current_user)):
    return e_t_f.get_final_statuses(current_user)


@router.post("/check-device-token")
async def check_device_token_route(
        request: ETs.RequestCheckDeviceToken,
) -> ETs.ResponseCheckDeviceToken:
    return await e_t_f.check_device_token(request)
