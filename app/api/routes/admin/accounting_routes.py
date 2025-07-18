from fastapi import APIRouter, Depends
from starlette.responses import Response

from datetime import datetime, timedelta
from typing import List
from app import exceptions
from app.repositories.transactions_repository import TransactionsRepository
from app.schemas.ExternalTransactionScheme import (
    ExportSumTransactionsResponse
)

from app.core.constants import Role
from app.enums import Permission
from app.api import deps
from app.functions.admin.accounting_services import (
    get_accounting_user,
    get_list_accounting
)
from app.repositories.admin import geo_repository
from app.functions.admin.export_service import export_transactions_to_csv, export_transactions_csv_stream
from app.schemas.UserScheme import UserSupportScheme
from app.schemas.admin.AccountingScheme import (
    ListResponseAccounting,
    FilterAccountingScheme,
    DownloadAccountingScheme
)

router = APIRouter()

@router.get("/list")
async def list_accounting_users(
    last_offset_id: int,
    limit: int,
    role: str | None = None,
    geo_id: int | None = None,
    search: str | None = None,
    current_user: UserSupportScheme = Depends(
        deps.v2_get_current_support_user_with_permissions([
            Permission.VIEW_ACCOUNTING
        ])
    )
) -> ListResponseAccounting:
    request = FilterAccountingScheme(last_offset_id=last_offset_id, limit=limit, role=role, geo_id=geo_id, search=search)
    list_accounting_users = await get_list_accounting(request=request, namespace_id=current_user.namespace.id)
    return list_accounting_users


@router.post("/get/{id}")
async def get_accounting(
    id: str,
    request: DownloadAccountingScheme,
    current_user: UserSupportScheme = Depends(
        deps.v2_get_current_support_user_with_permissions([
            Permission.VIEW_ACCOUNTING
        ])
    )
) -> Response:
    name, balance, role, balance_id = await get_accounting_user(id=id)

    if role not in [Role.TEAM, Role.MERCHANT, Role.AGENT]:
        raise exceptions.UserWrongRoleException(roles=[Role.TEAM, Role.MERCHANT, Role.AGENT])

    if request.create_timestamp_from is None:
        request.create_timestamp_from = (datetime.now() - timedelta(days=30)).timestamp()
    if request.create_timestamp_to is None:
        request.create_timestamp_to = datetime.now().timestamp()

    transactions_gen = TransactionsRepository.batched_transactions_generator(
        balance_id=balance_id,
        role=role,
        from_ts=request.create_timestamp_from,
        to_ts=request.create_timestamp_to,
    )

    date_from = datetime.utcfromtimestamp(request.create_timestamp_from)
    date_to = datetime.utcfromtimestamp(request.create_timestamp_to)
    date_from_str = date_from.strftime('%d-%m-%Y')
    date_to_str = date_to.strftime('%d-%m-%Y')
    filename = f'{name}-[{date_from_str}]-[{date_to_str}]_{balance}USDT.csv'

    return await export_transactions_csv_stream(
        transactions_gen=transactions_gen,
        name=name if role != Role.MERCHANT else None,
        role=role,
        filename=filename
    )


@router.get("/download")
async def get_accounting_users(role: str | None = None,
                               geo_id: int | None = None,
                               search: str | None = None,
                               current_user: UserSupportScheme = Depends(
                                   deps.v2_get_current_support_user_with_permissions([
                                       Permission.VIEW_ACCOUNTING
                                   ])
                               )
                               ) -> Response:
    request = FilterAccountingScheme(role=role, geo_id=geo_id, search=search)
    result = await get_list_accounting(request=request, namespace_id=current_user.namespace.id)
    csv_bytes = await export_transactions_to_csv(result.items)
    if request.geo_id:
        geo = ""
        geo_list = await geo_repository.get_all(namespace_id=current_user.namespace.id)
        for geo_elem in geo_list:
            if geo_elem.id == request.geo_id:
                geo = geo_elem.name
    else:
        geo = "All"
    now = datetime.utcnow()
    formatted_date = now.strftime("%d-%m-%Y-%H:%M")
    headers = {'Content-Disposition': f'attachment; filename="[{formatted_date}]Accounting{geo if request.search is None else ""}{(request.role.capitalize() if request.role else "Users") if request.search is None else ""}{"WithSearch" if request.search else ""}.csv"'}
    return Response(csv_bytes, media_type='application/ms-excel', headers=headers)
