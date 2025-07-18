from fastapi import APIRouter, Depends

from app import exceptions as exceptions
from app.api import deps
from app.api.deps import v2_get_current_team_user
from app.core.constants import Role, Limit, Type, get_class_fields
import app.functions.bank_detail as b_d_f
import app.schemas.BankDetailScheme as BDs
import app.schemas.UserScheme as Us
from app.schemas.UserScheme import UserTeamScheme
import datetime

router = APIRouter()


@router.post("/create")
async def create_route(
        bank_detail: BDs.BankDetailSchemeRequestCreate,
        current_user: UserTeamScheme = Depends(v2_get_current_team_user),
) -> BDs.BankDetailSchemeResponse:
    """Create new bank detail. Available for user with role \"team\"."""
    if bank_detail.fiat_max_inbound:
        bank_detail.fiat_max_inbound = min(bank_detail.fiat_max_inbound, 4294967295)
    if bank_detail.type not in get_class_fields(Type):
        raise exceptions.WrongTypeException()
    if bank_detail.period_time is not None:
        bank_detail.period_start_time = datetime.time(hour=bank_detail.period_time[0] // 60, minute=bank_detail.period_time[0] % 60)
        bank_detail.period_finish_time = datetime.time(hour=bank_detail.period_time[1] // 60, minute=bank_detail.period_time[1] % 60)
    result = await b_d_f.create_bank_detail(
        BDs.BankDetailSchemeRequestCreateDB(team_id=current_user.id, **bank_detail.__dict__))
    return result


@router.get("/list")
async def list_route(
        last_offset_id: int,
        limit: int,
        search: str | None = None,
        currency_id: str | None = None,
        bank: str | None = None,
        payment_system: str | None = None,
        is_active: bool | None = None,
        is_vip: str | None = None,
        current_user: UserTeamScheme = Depends(v2_get_current_team_user),
) -> BDs.BankDetailSchemeResponseList:
    """List bank details. Using pagination: Items with id LESS than <b>last_offset_id</b>. Items amount is
    <b>limit</b> or less if it is end. Available for user with role \"team\"."""
    if is_vip == "true":
        is_vip_bool = True
    elif is_vip == "false":
        is_vip_bool = False
    else:
        is_vip_bool = None
    bank_detail_params = BDs.BankDetailSchemeRequestList(
        limit=limit,
        last_offset_id=last_offset_id,
        search=search,
        currency_id=currency_id,
        bank=bank,
        payment_system=payment_system,
        is_active=is_active,
        is_vip=is_vip_bool
    )
    
    if bank_detail_params.limit > Limit.MAX_ITEMS_PER_QUERY:
        raise exceptions.ListResponseLengthLimitException
    
    result = await b_d_f.list_bank_detail(
        BDs.BankDetailSchemeRequestListDB(team_id=current_user.id, **bank_detail_params.__dict__))
    return result


@router.get("/list_profiles")
async def list_profiles(
    bank: str | None = None,
    device_hash: str | None = None,
    current_user: UserTeamScheme = Depends(v2_get_current_team_user)
) -> BDs.BankDetailProfilesResponseList:
    result = await b_d_f.list_profiles(
        bank=bank, device_hash=device_hash, team_id=current_user.id
    )
    return result


@router.delete("/delete")
async def delete_route(
        bank_detail_params: BDs.BankDetailSchemeRequestDelete,
        current_user: UserTeamScheme = Depends(v2_get_current_team_user),
) -> BDs.BankDetailSchemeResponse:
    """Delete bank details by id. Available for user with role \"team\"."""
    result = await b_d_f.delete_bank_detail(
        BDs.BankDetailSchemeRequestDeleteDB(team_id=current_user.id, **bank_detail_params.__dict__))
    return result


@router.patch("/{id}")
async def update_route(
        id: str,
        bank_detail: BDs.BankDetailSchemeResponseUpdateID,
        current_user: UserTeamScheme = Depends(v2_get_current_team_user),
) -> BDs.BankDetailSchemeResponse:
    """Update bank details. Available for user with role \"team\"."""
    if bank_detail.fiat_max_inbound:
        bank_detail.fiat_max_inbound = min(bank_detail.fiat_max_inbound, 4294967295)
    if bank_detail.type and bank_detail.type not in get_class_fields(Type):
        raise exceptions.WrongTypeException()
    if bank_detail.period_time is not None:
        bank_detail.period_start_time = datetime.time(hour=bank_detail.period_time[0] // 60,
                                                      minute=bank_detail.period_time[0] % 60)
        bank_detail.period_finish_time = datetime.time(hour=bank_detail.period_time[1] // 60,
                                                       minute=bank_detail.period_time[1] % 60)
    result = await b_d_f.update_bank_detail(
        BDs.BankDetailSchemeRequestUpdateDB(id=id, team_id=current_user.id, **bank_detail.__dict__))
    return result

@router.get("/{id}")
async def get_route(
    id: str,
    current_user: UserTeamScheme = Depends(v2_get_current_team_user),
) -> BDs.BankDetailSchemeResponse:
    return await b_d_f.get_bank_detail(
        id=id
    )


@router.get("/statistic/{id}")
async def get_statistic(
    id: str,
    current_user: UserTeamScheme = Depends(v2_get_current_team_user),
) -> BDs.BankDetailStatisticSchemeResponse:
    return await b_d_f.get_statistic_detail(
        id, user_id=current_user.id
    )