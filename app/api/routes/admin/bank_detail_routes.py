from typing import List

from fastapi import APIRouter, Depends

from app.api.deps import v2_get_current_support_user_with_permissions, v2_get_current_user
from app.functions.admin.details_services import (
    list_bank_details,
    update_bank_details,
)
from app.enums import Permission
from app.schemas.admin.DetailsScheme import *
from app.schemas.UserScheme import UserSupportScheme, User
from app.core.constants import TrafficStatsPeriodName

router = APIRouter()

@router.get("/")
async def list(
    last_offset_id: int,
    limit: int,
    period_name: TrafficStatsPeriodName,
    search: str | None = None,
    type: str | None = None,
    bank: str | None = None,
    payment_system: str | None = None,
    is_vip: str | None = None,
    is_active: bool | None = None,
    team_id: str | None = None,
    geo_id: int | None = None,
    current_user: User = Depends(v2_get_current_user)
) -> BankDetailSchemeResponseList:
    if is_vip == "true":
        is_vip_bool = True
    elif is_vip == "false":
        is_vip_bool = False
    else:
        is_vip_bool = None
    period = 15 if period_name == "15 min" else 60 if period_name == "hour" else 1440 if period_name == "24h" else 0
    print(period)
    bank_detail_params = AdminBankDetailSchemeRequestList(
        limit=limit,
        last_offset_id=last_offset_id,
        search=search,
        type=type,
        bank=bank,
        payment_system=payment_system,
        is_active=is_active,
        team_id=team_id,
        period=period,
        is_vip=is_vip_bool,
        geo_id=geo_id
    )
    details: BankDetailSchemeResponseList = await list_bank_details(
        namespace_id=current_user.namespace.id, filter=bank_detail_params
    )
    return details


@router.patch("/{id}")
async def update(
    id: str,
    period_name: TrafficStatsPeriodName,
    request: AdminUpdateDetailRequestScheme,
        current_user: UserSupportScheme = Depends(
            v2_get_current_support_user_with_permissions([
                Permission.VIEW_DETAILS
            ])
        )
) -> AdminBankDetailSchemeResponse:
    if request.fiat_max_inbound:
        request.fiat_max_inbound = min(request.fiat_max_inbound, 4294967295)
    period = 15 if period_name == "15 min" else 60 if period_name == "hour" else 1440 if period_name == "24h" else 0
    data = request.model_dump(exclude_unset=True)
    agent: AdminBankDetailSchemeResponse = await update_bank_details(
        detail_id=id, period=period, **data
    )
    return agent

#
