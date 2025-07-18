import uuid
from sqlalchemy import select

import os
from aiogram.enums import currency
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import app.exceptions as exceptions
import app.functions.external_transaction as e_t_f
import app.schemas.ExternalTransactionScheme as ETs
import app.schemas.UserScheme as Us
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.constants import Role, Status, Direction, Type, get_class_fields
from app.core.session import async_session
from app.functions.user import user_get_by_api_secret
from app.models import CurrencyModel
from app.schemas.v2.ExternalTransactionScheme import H2HCreateInbound, H2HCreateOutbound, H2HOutboundResponse

router = APIRouter()


@router.post("/payer-access-token")
async def get_access_token(
        request: Us.RequestCreatePaymentByApiSecret = Depends(),
):
    user = await user_get_by_api_secret(
        Us.UserSchemeRequestGetByApiSecret(api_secret=request.api_secret))
    if user.role != Role.MERCHANT:
        raise exceptions.UserWrongRoleException(roles=[Role.MERCHANT])
    async with async_session() as session:
        currency_name_q = await session.execute(
            select(CurrencyModel.name).filter(
                CurrencyModel.id == user.currency_id
            )
        )
        currency_name = currency_name_q.scalars().first()

    result = security.generate_access_token_response(
        type=request.type,
        role=user.role,
        merchant_transaction_id=request.merchant_transaction_id,
        hook_uri=request.hook_uri,
        access_token_expires_s=settings.PAYER_ACCESS_TOKEN_EXPIRE_S,
        refresh_token_expires_s=0,
        user_role=user.role,
        merchant_id=user.id,
        payer_id=request.payer_id,
        amount=request.amount,
        currency_id=currency_name,
        return_url=request.return_url,
        merchant_website_name=request.merchant_website_name
    )
    return result


@router.post("/create")
async def create_external_transaction_open_route(
        request: Request,
        create: ETs.RequestCreatePayment,
        payment_info: Us.PaymentSchemeResponse = Depends(deps.get_current_payment),
) -> ETs.PaymentFormResponse:
    """Create new external transaction. Available for user with role \"team\"."""
    if payment_info.user_role != Role.MERCHANT:
        raise exceptions.UserWrongRoleException(roles=[Role.MERCHANT])
    
    if create.type not in get_class_fields(Type):
        raise exceptions.WrongTypeException()
    
    transaction = await e_t_f.h2h_create_inbound(
        H2HCreateInbound(
            **payment_info.__dict__,
            merchant_payer_id=payment_info.payer_id,  # TODO убрать костыль
            type=create.type,
        ),
        request
    )
    return ETs.PaymentFormResponse(
        bank_icon_url=f'/payment-form/bank-icon/{transaction.bank_detail.bank}',
        amount=transaction.amount,
        currency_id=transaction.currency_id,
        id=transaction.id,
        create_timestamp=transaction.create_timestamp,
        status=transaction.status,
        bank_detail_number=transaction.bank_detail.number,
        bank_detail_bank=transaction.bank_detail.bank,
        bank_detail_name=transaction.bank_detail.name,
        transaction_auto_close_time_s=transaction.transaction_auto_close_time_s,
    )


@router.post("/create-outbound")
async def create_external_transaction_open_route(
        create: ETs.RequestCreatePaymentOutbound,
        payment_info: Us.PaymentSchemeResponse = Depends(deps.get_current_payment),
) -> H2HOutboundResponse:
    """Create new external transaction. Available for user with role \"team\"."""
    if payment_info.user_role != Role.MERCHANT:
        raise exceptions.UserWrongRoleException(roles=[Role.MERCHANT])
    
    if create.type not in get_class_fields(Type):
        raise exceptions.WrongTypeException()
    
    transaction = await e_t_f.h2h_create_outbound(
        H2HCreateOutbound(
            **payment_info.__dict__,
            merchant_payer_id=payment_info.payer_id,  # TODO убрать костыль
            type=create.type,
            bank_detail_number=create.bank_detail_number,
            bank_detail_bank=create.bank_detail_bank,
            bank_detail_name=create.bank_detail_name
        )
    )
    return transaction


@router.get('/bank-icon/{bank}')
async def get_bank_icon(
        bank: str) -> FileResponse:
    """Get bank icon"""
    try:
        svg_path = f'app/api/static/banks_icons/{bank}.svg'
        if os.path.exists(svg_path):
            return FileResponse(svg_path)

        png_path = f'app/api/static/banks_icons/{bank}.png'
        if os.path.exists(png_path):
            return FileResponse(png_path)

        raise FileNotFoundError
    except FileNotFoundError:
        return FileResponse(f'app/api/static/banks_icons/other.svg')


@router.get("/status")
async def create_external_transaction_open_route(
        transaction_id: str,
        payment_info: Us.PaymentSchemeResponse = Depends(deps.get_current_payment),
) -> ETs.StatusResponse:
    """Get status"""
    if payment_info.user_role != Role.MERCHANT:
        raise exceptions.UserWrongRoleException(roles=[Role.MERCHANT])
    
    result = await e_t_f.find_external_transaction_status(
        transaction_id=transaction_id,
        merchant_id=payment_info.merchant_id
    )
    return result


@router.get("/order")
async def create_external_transaction_order_route(
        transaction_id: str,
        payment_info: Us.PaymentSchemeResponse = Depends(deps.get_current_payment),
) -> ETs.PaymentFormResponse:
    """Order."""
    if payment_info.user_role != Role.MERCHANT:
        raise exceptions.UserWrongRoleException(roles=[Role.MERCHANT])
    
    result = await e_t_f.find_external_transaction_by_id(
        transaction_id=transaction_id,
        merchant_id=payment_info.merchant_id
    )
    result.bank_icon_url = f'/payment-form/bank-icon/{result.bank_detail_bank}'
    
    return result
