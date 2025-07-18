from typing import List
from fastapi import APIRouter, Depends

from app import exceptions
from app.api.deps import v2_get_current_support_user
from app.functions.admin.merchant_services import (
    create_and_get_merch_user,
    list_merchant_users,
    update_merchant_user,
    regenerate_merchant_user
)
from app.core.constants import Role
from app.functions.admin.team_service import list_users_balance_info
from app.functions.namespace import get_currency_for_merchants_by_geo
from app.schemas.GenericScheme import GenericListResponseWithTypes
from app.schemas.admin.MerchantScheme import (
    CreateMerchantRequestScheme,
    UpdateMerchantRequestScheme,
    V2MerchantResponseScheme
)
from app.schemas.admin.TeamScheme import (
    InfoBalanceScheme
)
from app.schemas.UserScheme import UserSupportScheme

router = APIRouter()


@router.post("/")
async def create(
    request: CreateMerchantRequestScheme,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> V2MerchantResponseScheme:
    merch: V2MerchantResponseScheme = await create_and_get_merch_user(
        name=request.name,
        namespace_id=current_user.namespace.id,
        currency_id=request.rate_model,
        credit_factor=request.limit,
        geo_id=request.geo_id,
        balance_id=request.balance_id
    )
    return merch


@router.get("/")
async def list(
    geo_id: int | None = None,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user)
) -> GenericListResponseWithTypes[V2MerchantResponseScheme]:
    merch_users: List[V2MerchantResponseScheme] = await list_merchant_users(
        geo_id=geo_id, namespace_id=current_user.namespace.id
    )

    currencies = await get_currency_for_merchants_by_geo(geo_id)

    return GenericListResponseWithTypes(types=currencies, items=merch_users)


@router.get("/balances")
async def list_balances(
    geo_id: int | None = None,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> List[InfoBalanceScheme]:
    merch_users: List[InfoBalanceScheme] = await list_users_balance_info(
        geo_id=geo_id,
        namespace_id=current_user.namespace.id,
        role=Role.MERCHANT
    )

    return merch_users


@router.patch("/{id}")
async def update(
    id: str,
    request: UpdateMerchantRequestScheme,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> V2MerchantResponseScheme:
    data = request.model_dump(exclude_unset=True)

    merch: V2MerchantResponseScheme = await update_merchant_user(
        user_id=id, role=Role.MERCHANT, **data
    )

    return merch

@router.patch("/regenerate/{id}")
async def regenerate(
    id: str,
    current_user=Depends(v2_get_current_support_user),
) -> V2MerchantResponseScheme:
    if current_user.role != Role.SUPPORT:
        raise exceptions.UserWrongRoleException(roles=[Role.SUPPORT])

    merchant_user: V2MerchantResponseScheme = await regenerate_merchant_user(
        merchant_id=id
    )

    return merchant_user
