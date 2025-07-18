from typing import List

from fastapi import APIRouter, Depends

from app.api.deps import v2_get_current_support_user_with_permissions
from app.enums import Permission
from app.functions.admin.base_services import (
    batch_create_fee_contracts_service,
)
from app.repositories.admin.admin_repository import filter_fee_contracts_repo
from app.schemas.admin.FeeContractScheme import (
    FeeContractResponse,
    FeeContractsBatchCreateRequest,
)
from app.schemas.GenericScheme import GenericListResponseWithTypes
from app.schemas.UserScheme import UserSupportScheme

router = APIRouter()


@router.get("/")
async def list_fee_contracts(
    merchant_id: str,
    team_id: str,
    tag_id: str,
    current_user: UserSupportScheme = Depends(
        v2_get_current_support_user_with_permissions([Permission.VIEW_FEE])
    )
) -> GenericListResponseWithTypes[FeeContractResponse]:
    fee_contracts: [List[str], List[FeeContractResponse]] = await filter_fee_contracts_repo(
        merchant_id=merchant_id,
        team_id=team_id,
        tag_id=tag_id,
        namespace_id=current_user.namespace.id,
    )
    return GenericListResponseWithTypes(types=fee_contracts[0], items=fee_contracts[1])


@router.post("/")
async def replace_fee_contracts(
    request: FeeContractsBatchCreateRequest,
    current_user: UserSupportScheme = Depends(
        v2_get_current_support_user_with_permissions([Permission.VIEW_FEE])
    )
) -> GenericListResponseWithTypes[FeeContractResponse]:
    """
    Транзакционный batch запрос:
    1) удаляет fee contracts для пары мерчант-команды и всех агентов.
    2) создает объекты указанных типов.
    3) возвращает список созданных объектов
    """
    await batch_create_fee_contracts_service(
        merchant_id=request.merchant_id,
        team_id=request.team_id,
        tag_id=request.tag_id,
        fee_contracts=request.fee_contracts
    )

    fee_contracts: [List[str], List[FeeContractResponse]] = await filter_fee_contracts_repo(
        merchant_id=request.merchant_id,
        team_id=request.team_id,
        tag_id=request.tag_id,
        namespace_id=current_user.namespace.id,
    )
    return GenericListResponseWithTypes(types=fee_contracts[0], items=fee_contracts[1])
