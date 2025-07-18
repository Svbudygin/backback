from typing import List
from fastapi import APIRouter, Depends
from starlette.responses import Response

from app import exceptions
from app.api.deps import v2_get_current_user
from app.core.constants import Role
from app.functions.admin.export_service import export_transactions_csv_stream, export_transactions_to_csv
from app.repositories.transactions_repository import TransactionsRepository
from app.schemas.ExternalTransactionScheme import (
    ExportSumTransactionsResponse,
    ExportTransactionsRequest,
    ExportTransactionsResponse,
)
from app.schemas.InternalTransactionScheme import ExportInternalTransactionsRequest
from app.schemas.UserScheme import UserSchemeResponse, User

router = APIRouter()


@router.get("/transactions/")
async def export_transactions(
    status: str | None = None,
    direction: str | None = None,
    amount_from: int | None = None,
    amount_to: int | None = None,
    currency_id: str | None = None,
    create_timestamp_from: int | None = None,
    create_timestamp_to: int | None = None,
    current_user: User = Depends(v2_get_current_user),
) -> Response:
    role = current_user.role
    if role not in [Role.TEAM, Role.MERCHANT]:
        raise exceptions.UserWrongRoleException(roles=[Role.TEAM, Role.MERCHANT])

    request = ExportTransactionsRequest(
        user_id=current_user.id,
        status=status,
        direction=direction,
        role=role,
        amount_from=amount_from,
        amount_to=amount_to,
        currency_id=currency_id,
        create_timestamp_from=create_timestamp_from,
        create_timestamp_to=create_timestamp_to,
    )
    transactions: List[ExportTransactionsResponse] = (
        await TransactionsRepository.filter_external_transactions_for_export(request)
    )
    csv_bytes = await export_transactions_to_csv(transactions)
    headers = {"Content-Disposition": 'attachment; filename="transactions.csv"'}
    return Response(csv_bytes, media_type="application/ms-excel", headers=headers)


@router.get("/transactions/sum")
async def export_transactions_sum_route(
    create_timestamp_from: int | None = None,
    create_timestamp_to: int | None = None,
    current_user: User = Depends(v2_get_current_user),
):
    role = current_user.role
    if role not in [Role.TEAM, Role.MERCHANT, Role.AGENT]:
        raise exceptions.UserWrongRoleException(roles=[Role.TEAM, Role.MERCHANT])

    transactions_gen = TransactionsRepository.batched_transactions_generator(
        balance_id=current_user.balance_id,
        role=current_user.role,
        from_ts=create_timestamp_from,
        to_ts=create_timestamp_to,
    )

    filename = "transactions.csv"
    return await export_transactions_csv_stream(
        transactions_gen=transactions_gen,
        role=role,
        filename=filename
    )


@router.get("/transactions_internal/")
async def export_transactions_in_csv(
    user_id: str | None = None,
    status: str | None = None,
    direction: str | None = None,
    amount_from: int | None = None,
    amount_to: int | None = None,
    current_user: User = Depends(v2_get_current_user),
) -> Response:
    role = current_user.role
    request = ExportInternalTransactionsRequest(
        user_id=current_user.id if user_id is None else user_id,
        status=status,
        direction=direction,
        amount_from=amount_from,
        amount_to=amount_to,
        role=role,
    )
    transactions: List[ExportTransactionsResponse] = (
        await TransactionsRepository.filter_internal_transactions_for_export(request)
    )
    csv_bytes = await export_transactions_to_csv(transactions)
    headers = {"Content-Disposition": 'attachment; filename="transactions.csv"'}
    return Response(csv_bytes, media_type="application/ms-excel", headers=headers)

