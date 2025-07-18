import base64
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.utils.crypto import decrypt_fernet, encrypt_base64_with_key


templates = Jinja2Templates(directory="app/templates")


router = APIRouter()


@router.get('/sber/{data}')
async def sber_payment_link(request: Request, data: str):
    decrypted_data = decrypt_fernet(data)

    phone_number = decrypted_data['phone_number']
    amount = decrypted_data['amount']
    transaction_type = decrypted_data['type']

    val = encrypt_base64_with_key(f"{phone_number}|{str(amount / 1000000)}|{transaction_type}")

    response = templates.TemplateResponse(
        name="sber-payment.html",
        request=request,
        context={"val": val}
    )

    return response


@router.get("/tpay/{data}")
async def tpay_payment_link(request: Request, data: str):
    decrypted_data = decrypt_fernet(data)

    phone_number = decrypted_data['phone_number']
    amount = decrypted_data['amount']
    bank = decrypted_data['bank']

    val = encrypt_base64_with_key(f"{phone_number}|{str(amount / 1000000)}|{bank}")

    response = templates.TemplateResponse(
        name="tpay.html",
        request=request,
        context={"val": val}
    )

    return response
