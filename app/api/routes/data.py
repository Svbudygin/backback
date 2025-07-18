import time
from typing import Any

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from app.schemas.UserScheme import User
from app.api.deps import v2_get_current_user
from app.core.constants import Banks, Bank, Type, get_class_fields, Currency, Limit, DECIMALS, CACHE_TIMEOUT_SMALL_S, \
    Direction, Role, \
    DETAILS_INFO, USUAL_TYPES_INFO, SUPPORT_TYPES_INFO
from app.core.session import async_session
from app.functions.external_transaction import get_team_by_transaction_id
from app.models import ExternalTransactionModel, UserModel
from fastapi.responses import RedirectResponse
from app import exceptions
from fastapi_cache.decorator import cache
import app.schemas.ExternalTransactionScheme as ETs
import app.functions.external_transaction as e_t_f
from app.schemas.BalanceScheme import UpdateCurrencyRequest, UpdateCurrencyResponse
from app.functions import balance as b_f

router = APIRouter()


@router.get("/currency/list")
async def create_external_transaction_open_route() -> list[str]:
    return [attr for attr in dir(Currency)
            if not attr.startswith('__')]


@router.get("/usdt-exchange-rate/")
@cache(expire=CACHE_TIMEOUT_SMALL_S)
async def exchange_rate_route(
        _=Depends(v2_get_current_user)
) -> list[dict]:
    return []


@router.get('/bank/list')
async def create_external_transaction_banks_route() -> list:
    return [bank.name for bank in Banks.__dict__.values() if isinstance(bank, Bank)]


@router.get('/bank/associates-list/{geo}')
async def create_external_transaction_banks_associates_list(geo: str) -> dict:
    return {bank.name: bank.display_name if bank.display_name is not None else bank.name for bank in Banks.__dict__.values() if isinstance(bank, Bank) and bank.currency == geo}


@router.get('/details/info/{geo}')
async def get_details_info(geo: str, current_user: User = Depends(v2_get_current_user)) -> dict:
    type_codes = DETAILS_INFO[geo]["types"]
    types_info = SUPPORT_TYPES_INFO if current_user.role == Role.SUPPORT else USUAL_TYPES_INFO
    result = DETAILS_INFO[geo].copy()
    result["types"] = [types_info.get(t, t) for t in type_codes]
    return result


@router.get('/type/info/{geo}')
async def get_type_info(geo: str, current_user: User = Depends(v2_get_current_user)):
    type_codes = DETAILS_INFO[geo]["types"]
    types_info = SUPPORT_TYPES_INFO if current_user.role == Role.SUPPORT else USUAL_TYPES_INFO
    return [types_info.get(t, t) for t in type_codes]


@router.get('/banks/info/{geo}')
async def get_banks_info(geo: str, current_user: User = Depends(v2_get_current_user)):
    banks_info = DETAILS_INFO[geo]["banks"]
    return {"banks": banks_info}


@router.get('/type/list')
async def create_external_transaction_banks_route() -> list:
    return get_class_fields(Type)


@router.post('/echo')
async def request_echo(request: dict) -> dict:
    return request


@router.put('/currency/update')
async def update_currency(request: UpdateCurrencyRequest,
                          current_user: User = Depends(v2_get_current_user),
                          ) -> UpdateCurrencyResponse:
    if current_user.role != Role.B_WORKER:
        raise exceptions.UserWrongRoleException(roles=[Role.B_WORKER])
    result = await b_f.update_currency(request)
    return result


@router.get('/demo-link')
async def demo_link():
    import requests

    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
    }

    params = {
        'api_secret': 'kjh322k3245k525252lg1lfslsfgg42',
        'payer_id': f'efdfd{time.time()}',
        'amount': '1011000000',
        'currency_id': 'RUB',
    }

    response = requests.post('https://api.fsd.beauty/payment-form/payer-access-token',
                             params=params,
                             headers=headers)
    return RedirectResponse(url=f'https://worldkassa.xyz/?token={response.json()["access_token"]}')


@router.get('/query/{transaction_id}')
async def get_team_by_transaction_id_route(transaction_id: str) -> dict[str, Any]:
    if len(transaction_id) > Limit.MAX_STRING_LENGTH_SMALL:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    result = await get_team_by_transaction_id(transaction_id)
    return {
        "name": result.name,
        "direction": result.direction,
        "id": result.id,
        "merchant_transaction_id": result.merchant_transaction_id,
        "bank_detail_number": result.bank_detail_number,
        "bank_detail_bank": result.bank_detail_bank,
        "bank_detail_name": result.bank_detail_name,
        "amount": result.amount,
        "status": result.status,
    }


@router.put("/update")
async def update_transaction_route(
        update_scheme: ETs.RequestUpdateStatus,
) -> ETs.Response:
    if int(update_scheme.new_amount) == 0:
        update_scheme.new_amount = None
    async with async_session() as session:
        team_id_q = await session.execute(
            select(ExternalTransactionModel.team_id, ExternalTransactionModel.direction).filter(
                ExternalTransactionModel.id == update_scheme.transaction_id,
                ExternalTransactionModel.merchant_id == UserModel.id,
                UserModel.namespace == 'choza'
            )
        )
        r = team_id_q.first()
        if r is None:
            raise exceptions.UserNotFoundException()
        team_id, direction = r
        if direction != Direction.INBOUND:
            raise exceptions.ExternalTransactionExistingDirectionException([Direction.INBOUND])
    result = await e_t_f.external_transaction_update(
        ETs.RequestUpdateStatusDB(**update_scheme.__dict__, team_id=team_id))
    return result


@router.get('/{transaction_id}')
async def get_team_by_transaction_id_route(transaction_id: str) -> str:
    if len(transaction_id) > Limit.MAX_STRING_LENGTH_SMALL:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    result = await get_team_by_transaction_id(transaction_id)
    return f"""
Апелляция
команда: {result.name}
id (для поиcка) `{result.transaction_id}`
реквизит: `{result.bank_detail_number}`
банк: {result.bank_detail_bank}
имя: {result.bank_detail_name}
сумма: {round(result.amount / DECIMALS, 2)}

Ответьте на сообщение "подтверждено" или "отклонено".
""".replace('\n', '  \n')
