from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

import app.services.payment_form_service as payment_form_service
from app.schemas.PaymentFormScheme import CreatePaymentFormScheme, PaymentFormScheme, PaymentFormResponseScheme

# TODO: endpoint to form status

router = APIRouter()


@router.post("")
async def create_payment_form(
        req: Request,
        create_payment_form_scheme: CreatePaymentFormScheme
) -> PaymentFormScheme:
    return await payment_form_service.create_payment_form(req, create_payment_form_scheme)


@router.get("/{payment_form_id}")
async def get_form_by_id(payment_form_id: str) -> PaymentFormResponseScheme:
    return await payment_form_service.get_by_id(payment_form_id)


@router.post("/{payment_form_id}/methods/{code}")
async def apply_payment_method(req: Request, payment_form_id: str, code: str) -> PaymentFormResponseScheme:
    return await payment_form_service.apply_payment_method(req, payment_form_id, code)


@router.get('/{payment_form_id}/status')
async def get_form_status(payment_form_id: str) -> str:
    return await payment_form_service.get_payment_form_status(payment_form_id)


@router.get('/bank-icon/{bank}')
async def get_bank_icon(bank: str) -> FileResponse:
    return payment_form_service.get_bank_icon(bank)


@router.post('/{payment_form_id}/cancel')
async def cancel(payment_form_id: str) -> PaymentFormResponseScheme:
    return await payment_form_service.cancel(payment_form_id)
