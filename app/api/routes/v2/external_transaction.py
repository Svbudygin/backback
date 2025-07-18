from fastapi import APIRouter, Depends, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader
from fastapi_cache.decorator import cache
from starlette.responses import JSONResponse

from app import exceptions
from app.core.constants import CACHE_TIMEOUT_SMALL_S, Limit, Role, Type, get_class_fields
from app.functions import external_transaction as e_t_f
from app.functions.balance import get_balances_transaction, get_estimated_fiat_balance
from app.functions.user import user_get_by_api_secret, v2_user_get_merchant_by_api_secret
from app.schemas.UserScheme import (
    UserSchemeRequestGetBalances,
    UserSchemeRequestGetByApiSecret,
)
from app.schemas.v2 import ExternalTransactionScheme as ETs
from app.schemas.v2.ExternalTransactionScheme import H2HInboundResponse, H2HOutboundResponse, H2HGetResponse, \
    BalanceResponse, BalancesResponse

router: APIRouter = APIRouter()
token_auth_scheme = APIKeyHeader(name="x-token")


@router.post(path="/create/pay-in",
             description='''Creating transaction for pay in.<br/><br/>
<b>amount</b>: int - actual transaction amount multiplied by 1,000,000<br/>
<b>hook_uri</b>: string - your url for callback<br/>
<b>type</b>: string - one of ["card", "phone", "account", "iban"]<br/>
<b>tag_code</b>: string | null - one of ["default", "interbank"]. Used to identify fee rates<br/>
<b>merchant_payer_id</b>: string - id of the payer making the transaction<br/>
<b>merchant_transaction_id</b>: string - your id of the transaction<br/>
''',
             response_model=H2HInboundResponse)
async def create_pay_in_route(
        request: Request,
        create: ETs.H2HCreateInboundJWT,
        api_secret: str = Depends(token_auth_scheme),
):
    current_user = await v2_user_get_merchant_by_api_secret(api_secret)
    
    if not current_user.is_inbound_enabled:
        raise exceptions.UserNotEnabledException()
    
    if create.type and create.type not in get_class_fields(Type):
        raise exceptions.WrongTypeException()
    
    if create.amount < 0 or create.amount > Limit.MAX_INT:
        raise exceptions.WrongTransactionAmountException()
    return await e_t_f.h2h_create_inbound(
        ETs.H2HCreateInbound(**create.__dict__, merchant_id=current_user.id),
        request
    )


@router.post(path="/create/pay-out",
             description='''Creating transaction for pay out.<br/><br/>
<b>amount</b>: int - actual transaction amount multiplied by 1,000,000<br/>
<b>hook_uri</b>: string - your url for callback<br/>
<b>type</b>: string - one of ["card", "phone", "account", "iban"]<br/>
<b>tag_code</b>: string | null - one of ["default", "interbank"]. Used to identify fee rates<br/>
<b>merchant_payer_id</b>: string - id of the payer making the transaction<br/>
<b>merchant_transaction_id</b>: string - your id of the transaction<br/>
''',
             response_model=H2HOutboundResponse)
async def create_outbound_route(
        create: ETs.H2HCreateOutboundJWT, api_secret: str = Depends(token_auth_scheme)
):
    current_user = await v2_user_get_merchant_by_api_secret(api_secret)
    
    if not current_user.is_outbound_enabled:
        raise exceptions.UserNotEnabledException()
    
    if create.type and create.type not in get_class_fields(Type):
        raise exceptions.WrongTypeException()
    
    if create.amount < 0 or create.amount > Limit.MAX_INT:
        raise exceptions.WrongTransactionAmountException()

    return await e_t_f.h2h_create_outbound(
        ETs.H2HCreateOutbound(
            **create.__dict__,
            currency_id=current_user.currency_id,
            merchant_id=current_user.id
        )
    )


@router.get(path="/get/",
            description='''Creating transaction for pay out.<br/><br/>
<b>id</b>: string | None - our id of the transaction<br/>
<b>merchant_transaction_id</b>: string | None - your id of the transaction<br/>
⚠️ One of "id", "merchant_transaction_id" is mandatory.
''',
            response_model=H2HGetResponse)
async def get_external_transactions(
        id: str | None = None,
        merchant_transaction_id: str | None = None,
        api_secret: str = Depends(token_auth_scheme),
):
    current_user = await v2_user_get_merchant_by_api_secret(api_secret)
    
    return await e_t_f.h2h_get_transaction_info(
        ETs.H2HGetRequest(
            merchant_id=current_user.id,
            id=id,
            merchant_transaction_id=merchant_transaction_id,
        )
    )


@router.get(path="/balances/",
            description='''Get usdt balances.<br/><br/>
<b>balance</b>: your current USDT-balance<br/>
<b>locked_balance</b>: your current locked USDT-balance<br/>
⚠️ You need to divide the balance from the response by 1000000 to get your real balance<br/>
⚠️ You need to divide the locked_balance from the response by 1000000 to get your real locked_balance
''')
async def get_balances(api_secret: str = Depends(token_auth_scheme)):
    current_user = await v2_user_get_merchant_by_api_secret(api_secret)

    balances = await get_balances_transaction(user_id=current_user.id)

    result = UserSchemeRequestGetBalances(
        trust_balance=balances[0],
        locked_balance=balances[1],
        profit_balance=balances[2],
        fiat_trust_balance=balances[3],
        fiat_locked_balance=balances[4],
        fiat_profit_balance=balances[5],
    )
    return BalancesResponse(balance=result.trust_balance,
                            locked_balance=result.locked_balance)


@router.get(path="/balances/estimated-fiat-trust-balance",
            description='''Get fiat balances.<br/><br/>
<b>balance</b>: your current fiat-balance<br/>
⚠️ You need to divide the balance from the response by 1000000 to get your real fiat balance<br/>
''')
async def get_balances(
        api_secret: str = Depends(token_auth_scheme),
):
    current_user = await v2_user_get_merchant_by_api_secret(api_secret)

    estimated_fiat_balance = await get_estimated_fiat_balance(
        user_id=current_user.id, currency_id=current_user.currency_id
    )

    return BalanceResponse(balance=estimated_fiat_balance)
