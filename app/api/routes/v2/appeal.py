from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, Form, Query
from fastapi.responses import StreamingResponse

from app.api.deps import (
    get_current_merchant_user_by_x_token,
    v2_get_current_user,
    get_current_user_by_x_token_or_bearer
)
from app.schemas.UserScheme import User, UserMerchantScheme
from app.schemas.AppealScheme import (
    AppealCreateScheme,
    AppealResponseScheme,
    AppealListFilterScheme,
    AppealUpdateScheme,
    CancelAppealRequestScheme,
    AcceptAppealRequestScheme
)
from app.schemas.PaginationScheme import PaginationParams
from app.schemas.GenericScheme import GenericListResponse
from app.core.constant.appeal_constants import (
    CATEGORIES_PARAM,
    SupportCategoriesEnum
)
import app.functions.appeal as appeal_service
from app.core.constants import Role
import app.exceptions as exceptions

router = APIRouter()


@router.get("/categories")
async def get_categories(
    current_user: User = Depends(v2_get_current_user),
    geo_id: Optional[int] = Query(default=None)
):
    return await appeal_service.get_categories(current_user, geo_id)


@router.get("/reject-reasons")
def get_appeal_reject_reasons(current_user: User = Depends(v2_get_current_user)):
    return appeal_service.get_appeal_reject_reasons(current_user)


@router.post("")
async def create(
        transaction_id: str = Form(),
        amount: Optional[int] = Form(None),
        merchant_appeal_id: Optional[str] = Form(None),
        finalization_callback_uri: Optional[str] = Form(None),
        ask_statement_callback_uri: Optional[str] = Form(None),
        files: List[UploadFile] = [],
        current_user: User = Depends(get_current_user_by_x_token_or_bearer),
) -> AppealResponseScheme:
    if current_user.role not in [Role.TG_APPEAL_WORKER, Role.MERCHANT]:
        return exceptions.UserWrongRoleException(roles=[Role.MERCHANT])
    return await appeal_service.create_appeal(
        current_user,
        AppealCreateScheme(
            transaction_id=transaction_id,
            amount=amount,
            merchant_appeal_id=merchant_appeal_id,
            finalization_callback_uri=finalization_callback_uri,
            ask_statement_callback_uri=ask_statement_callback_uri,
        ),
        files
    )


@router.get("")
async def get_all(
        current_user: User = Depends(get_current_user_by_x_token_or_bearer),
        pagination: PaginationParams = Depends(),
        filters: AppealListFilterScheme = Depends(),
        category: CATEGORIES_PARAM = SupportCategoriesEnum.PENDING
) -> GenericListResponse[AppealResponseScheme]:
    items = await appeal_service.get_appeals(current_user, pagination, filters, category)
    return GenericListResponse(items=items)


@router.get("/{appeal_id}")
async def get_by_id(
        appeal_id: str,
        current_user: User = Depends(get_current_user_by_x_token_or_bearer)
) -> AppealResponseScheme:
    return await appeal_service.get_appeal_by_id(appeal_id, current_user)


@router.post("/{appeal_id}/request-team-statement")
async def request_team_statement(
        appeal_id: str,
        current_user: User = Depends(v2_get_current_user)
) -> None:
    return await appeal_service.request_team_statement(appeal_id, current_user)


@router.post("/{appeal_id}/request-merchant-statement")
async def request_merchant_statement(
        appeal_id: str,
        current_user: User = Depends(v2_get_current_user)
) -> None:
    return await appeal_service.request_merchant_statement(appeal_id, current_user)


@router.post("/{appeal_id}/accept")
async def accept_appeal(
        appeal_id: str,
        data: AcceptAppealRequestScheme,
        current_user: User = Depends(v2_get_current_user)
):
    return await appeal_service.accept_appeal(appeal_id, data, current_user)


@router.post("/{appeal_id}/cancel")
async def cancel_appeal(
        appeal_id: str,
        data: CancelAppealRequestScheme,
        current_user: User = Depends(v2_get_current_user)
):
    return await appeal_service.cancel_appeal(appeal_id, data, current_user)


# @router.patch("/{appeal_id}")
# async def update_by_id(
#         appeal_id: str,
#         dto: AppealUpdateScheme,
#         current_user: User = Depends(v2_get_current_user)
# ) -> None:
#     return await appeal_service.update_appeal_by_id(appeal_id, dto, current_user)


@router.post("/{appeal_id}/upload-team-statement")
async def upload_team_statement(
    appeal_id: str,
    files: UploadFile,
    current_user: User = Depends(v2_get_current_user)
):
    return await appeal_service.upload_team_statement(appeal_id, files, current_user)


@router.post("/{appeal_id}/upload-merchant-statement")
async def upload_merchant_statement(
    appeal_id: str,
    files: UploadFile,
    current_user: User = Depends(get_current_user_by_x_token_or_bearer)
):
    return await appeal_service.upload_merchant_statement(appeal_id, files, current_user)


@router.get("/{appeal_id}/download-statement/{file_id}")
async def download_state(
    appeal_id: str,
    file_id: str,
    current_user: User = Depends(get_current_user_by_x_token_or_bearer)
) -> StreamingResponse:
    return await appeal_service.download_statement(appeal_id, file_id, current_user)


@router.get("/{appeal_id}/receipts")
async def get_receipts_links(
        appeal_id: str,
        current_user: User = Depends(v2_get_current_user)
) -> list[str]:
    return await appeal_service.get_receipts_links(appeal_id, current_user)
