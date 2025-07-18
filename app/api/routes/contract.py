from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from app.enums import Permission
from app.schemas.UserScheme import UserSupportScheme

from app.api import deps
from app.api.deps import v2_get_current_support_user_with_permissions
from app.core.constants import Role, Limit
from app.functions.user import user_get_by_id
from app.repositories.admin.admin_repository import make_copy_fee_contracts, bulk_fee_change
from app.schemas.UserScheme import UserSchemeResponse, UserSchemeRequestGetById
from app.schemas.admin.FeeContractScheme import FeeContractCopy, FeeContractBulkChange
from app.functions.contract import *
import app.exceptions as exceptions

traffic_weight_router = APIRouter()
fee_router = APIRouter()


async def check_field_validness_(
        contract_detail: (
                FeeRequestCreate |
                FeeRequestUpdate |
                TrafficWeightRequestCreate |
                TrafficWeightRequestUpdate
        )
):
    if type(contract_detail) in (FeeRequestCreate, TrafficWeightRequestCreate) or (
        contract_detail.team_id is not None
    ):
        team_candidate: UserSchemeResponse = await user_get_by_id(
            UserSchemeRequestGetById(id=contract_detail.team_id))
        if team_candidate is None or team_candidate.role != Role.TEAM:
            raise exceptions.UserNotFoundException
    
    if type(contract_detail) in (FeeRequestCreate, TrafficWeightRequestCreate) or (
        contract_detail.merchant_id is not None
    ):
        merchant_candidate = await user_get_by_id(
            UserSchemeRequestGetById(id=contract_detail.merchant_id))
        if merchant_candidate is None or merchant_candidate.role != Role.MERCHANT:
            raise exceptions.UserNotFoundException
    
    if type(contract_detail) is FeeRequestCreate or (
        type(contract_detail) is FeeRequestUpdate and contract_detail.user_id is not None
    ):
        user_candidate = await user_get_by_id(
            UserSchemeRequestGetById(id=contract_detail.user_id))
        if user_candidate is None:
            raise exceptions.UserNotFoundException


@fee_router.post("/create")
async def create_fee_contract_route(
        contract_detail: FeeRequestCreate,
        current_user: UserSchemeResponse = Depends(deps.get_current_user),
) -> FeeResponse:
    """Create new fee contract. Available for user with role \"root\"."""
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])
    
    await check_field_validness_(contract_detail)
    
    result = await create_fee_contract(
        FeeRequestCreate(**contract_detail.__dict__))
    return result


@traffic_weight_router.post("/create")
async def create_traffic_weight_contract_route(
        contract_detail: TrafficWeightRequestCreate,
        current_user: UserSchemeResponse = Depends(deps.get_current_user),
) -> TrafficWeightResponse:
    """Create new traffic-weight contract. Available for user with role \"root\"."""
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])
    
    await check_field_validness_(contract_detail)
    
    result = await create_traffic_weight_contract(
        TrafficWeightRequestCreate(**contract_detail.__dict__))
    return result


@fee_router.get("/list")
async def list_contract_detail_route(
        last_offset_id: int,
        limit: int,
        current_user: UserSchemeResponse = Depends(deps.get_current_user),
) -> FeeResponseList:
    """List fee contracts. Using pagination: Items with id LESS than <b>last_offset_id</b>. Items amount is
    <b>limit</b> or less if it is end. Available for user with role \"root\"."""
    
    contract_params = RequestList(
        limit=limit,
        last_offset_id=last_offset_id
    )
    
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])
    
    if contract_params.limit > Limit.MAX_ITEMS_PER_QUERY:
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                            detail=f'limit value can not be greater than {Limit.MAX_ITEMS_PER_QUERY}.')
    
    result = await list_fee_contract(
        RequestList(**contract_params.__dict__))
    return result


@traffic_weight_router.get("/list")
async def list_contract_detail_route(
        last_offset_id: int,
        limit: int,
        current_user: UserSchemeResponse = Depends(deps.get_current_user),
) -> TrafficWeightResponseList:
    """List traffic-weight contracts. Using pagination: Items with id LESS than <b>last_offset_id</b>. Items amount is
    <b>limit</b> or less if it is end. Available for user with role \"root\"."""
    
    contract_params = RequestList(
        limit=limit,
        last_offset_id=last_offset_id
    )
    
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])
    if contract_params.limit > Limit.MAX_ITEMS_PER_QUERY:
        raise exceptions.ListResponseLengthLimitException()
    
    result = await list_traffic_weight_contract(
        RequestList(**contract_params.__dict__))
    return result


@fee_router.delete("/delete")
async def list_contract_route(
        contract_params: RequestDelete,
        current_user: UserSchemeResponse = Depends(deps.get_current_user),
) -> FeeResponse:
    """Delete fee contract by id. Available for user with role \"root\"."""
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])
    
    result = await delete_fee_contract(
        RequestDelete(**contract_params.__dict__))
    if result is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Wrong fee contract id.")
    return result


@traffic_weight_router.delete("/delete")
async def list_contract_route(
        contract_params: RequestDelete,
        current_user: UserSchemeResponse = Depends(deps.get_current_user),
) -> TrafficWeightResponse:
    """Delete traffic-weight contract by id. Available for user with role \"root\"."""
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])
    
    result = await delete_traffic_weight_contract(
        RequestDelete(**contract_params.__dict__))
    if result is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Wrong traffic contract id.")
    return result


@fee_router.put("/update")
async def update_fee_contract_route(
        contract_params: FeeRequestUpdate,
        current_user: UserSchemeResponse = Depends(deps.get_current_user),
) -> FeeResponse:
    """Update fee contract details. Available for user with role \"ROOT\"."""
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])
    
    await check_field_validness_(contract_params)
    
    result = await update_fee_contract(
        FeeRequestUpdate(**contract_params.__dict__))
    if result is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Wrong fee contract id.")
    return result


@traffic_weight_router.put("/update")
async def update_traffic_weight_contract_route(
        contract_params: TrafficWeightRequestUpdate,
        current_user: UserSchemeResponse = Depends(deps.get_current_user),
) -> TrafficWeightResponse:
    """Update traffic-weight contract details. Available for user with role \"ROOT\"."""
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])
    
    await check_field_validness_(contract_params)
    
    result = await update_traffic_weight_contract(
        TrafficWeightRequestUpdate(**contract_params.__dict__))
    if result is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Wrong traffic contract id.")
    return result


@fee_router.post("/copy")
async def copy_fee_contracts(
        request: FeeContractCopy,
        current_user: UserSupportScheme = Depends(
            v2_get_current_support_user_with_permissions([Permission.VIEW_FEE])
        )
) -> JSONResponse:
    try:
        await make_copy_fee_contracts(
            merchant_id_from=request.merchant_id_from,
            merchant_id_to=request.merchant_id_to,
            tag_id=request.tag_id
        )
    except Exception as e:
        raise e
    return JSONResponse(status_code=200, content={"detail": "Fee contracts copied successfully"})


@fee_router.post("/bulk_fee_change")
async def change_fee_contracts(
        request: FeeContractBulkChange,
        current_user: UserSupportScheme = Depends(
            v2_get_current_support_user_with_permissions([Permission.VIEW_FEE])
        )
) -> JSONResponse:
    try:
        await bulk_fee_change(
            delta=request.delta,
            increase_id=request.increase_id,
            decrease_id=request.decrease_id,
            merchant_id=request.merchant_id,
            tag_id=request.tag_id,
            direction=request.direction
        )
    except Exception as e:
        raise e
    return JSONResponse(status_code=200, content={"detail": "Fee contracts changed successfully"})