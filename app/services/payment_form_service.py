import os
from typing import List, Optional
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.PaymentFormScheme import (
    CreatePaymentFormScheme,
    PaymentFormScheme,
    PaymentFormResponseScheme,
    PaymentFormNewResponseScheme,
    PaymentFormPendingResponseScheme,
    PaymentFormFinishResponseScheme,
    PaymentFormStatusEnum,
    PaymentFormConfigScheme
)
from app.schemas.v2.ExternalTransactionScheme import H2HCreateInbound
from app.models import (
    PaymentFormModel,
    ExternalTransactionModel,
    BankDetailModel,
    FeeContractModel
)
from app.core.session import ro_async_session, async_session
from app.core.constants import Status, ASSOCIATE_BANK, Banks, BANK_SCHEMAS, Type
from app.functions.external_transaction import h2h_create_inbound, external_transaction_update_
from app.functions.user import v2_user_get_merchant_by_api_secret
from app.enums import TransactionFinalStatusEnum

# TODO replace service with class, replace exceptions from constants
# TODO replace user v2_user_get_merchant_by_api_secret with Depends
# TODO replace payment_methods with external table

# TODO relocate constant to another place

METHODS_REQUIREMENTS = {
    'phone': {
        'types': [Type.PHONE],
        'banks': []
    },
    'card': {
        'types': [Type.CARD],
        'banks': []
    },
    'account': {
        'types': [Type.ACCOUNT],
        'banks': []
    },
    'sberpay': {
        'types': [Type.PHONE, Type.ACCOUNT],
        'banks': [Banks.SBER.name]
    },
    't-pay': {
        'types': [Type.PHONE],
        'banks': list(BANK_SCHEMAS.keys())
    },
    'cross-border-phone': {
        'types': [Type.CB_PHONE],
        'banks': []
    },
    'cbu': {
        'types': [Type.CBU],
        'banks': []
    },
    'cvu': {
        'types': [Type.CVU],
        'banks': []
    }
}


async def create_payment_form(
        req: Request,
        create_payment_form_scheme: CreatePaymentFormScheme
) -> PaymentFormScheme:
    async with (async_session() as session):
        user = await v2_user_get_merchant_by_api_secret(create_payment_form_scheme.api_secret)

        transaction_auto_close_time_s = user.transaction_auto_close_time_s
        currency_name = user.currency.name

        payment_form_data = create_payment_form_scheme.model_dump()
        payment_form_data["currency_name"] = currency_name
        payment_form_data["auto_close_time"] = transaction_auto_close_time_s
        del payment_form_data['api_secret']

        payment_form = PaymentFormModel(**payment_form_data, merchant_id=user.id)

        session.add(payment_form)

        await session.commit()

        await session.refresh(payment_form)

        if len(payment_form.config) == 1:
            await apply_payment_method(
                req,
                payment_form.id,
                payment_form.config[0]["name"]
            )

        for config in payment_form.config:
            if "options" in config:
                options = config["options"]
                if isinstance(options, dict):
                    banks = options.get("banks")
                    if banks is not None and isinstance(banks, list):
                        options["banks"] = [
                            ASSOCIATE_BANK.get(bank, bank)
                            for bank in banks
                        ]

        return PaymentFormScheme.model_validate(payment_form)


async def apply_payment_method(req: Request, payment_form_id: str, code: str) -> PaymentFormResponseScheme:
    async with (async_session() as session):
        payment_form: PaymentFormModel | None = (await session.execute(
            select(PaymentFormModel)
            .where(PaymentFormModel.id == payment_form_id)
        )).scalars().first()

        if payment_form is None:
            raise HTTPException(status_code=404, detail="Payment form not found")

        method = _get_method_by_name(payment_form.config, code)

        if method is None:
            raise HTTPException(status_code=400, detail="Invalid method")

        if not method["options"]:
            method["options"] = {
                "types": None,
                "banks": None,
                "payment_systems": None,
                "tag_code": None,
                "is_vip": False
            }

        external_transaction: ExternalTransactionModel | None = (await session.execute(
            select(ExternalTransactionModel)
            .where(ExternalTransactionModel.id == payment_form.id)
        )).scalars().first()

        if external_transaction is not None:
            raise HTTPException(status_code=400, detail="Invalid method")

        if method["name"] != 'sberpay' and method["name"] != 't-pay':
            types = None
        else:
            if method["options"]["types"] and len(method["options"]["types"]) > 0:
                types = method["options"]["types"]
            else:
                if method["name"] == 't-pay':
                    types = ['phone']
                else:
                    types = ['account', 'phone']

        if method["options"]["banks"] and len(method["options"]["banks"]) > 0:
            banks = method["options"]["banks"]
        else:
            banks = None

        if method["options"]["payment_systems"] and len(method["options"]["payment_systems"]) > 0:
            payment_systems = method["options"]["payment_systems"]
        else:
            payment_systems = None

        if method["name"] == 'sberpay':
            bank = 'sber'
        else:
            bank = None

        new_external_transaction = await h2h_create_inbound(H2HCreateInbound(
            amount=payment_form.amount,
            hook_uri=payment_form.hook_uri,
            tag_code=method["options"]["tag_code"],
            type=method["name"] if method["name"] != 'sberpay' and method["name"] != 't-pay' else None,
            types=types,
            bank=bank,
            banks=banks,
            payment_systems=payment_systems,
            merchant_id=payment_form.merchant_id,
            merchant_payer_id=payment_form.payer_id,
            merchant_transaction_id=payment_form.merchant_transaction_id,
            is_vip=method["options"]["is_vip"]
        ), req, payment_form.id)

        payment_form.method = method["name"]
        payment_form.links = new_external_transaction.payment_link
        payment_form.amount = new_external_transaction.amount

        await session.commit()

        return await get_by_id(payment_form_id, session)


async def get_by_id(payment_form_id: str, session: Optional[AsyncSession] = None) -> PaymentFormResponseScheme:
    if session is None:
        async with (ro_async_session() as new_session):
            return await _get_by_id(payment_form_id, new_session)
    else:
        return await _get_by_id(payment_form_id, session)


async def _get_by_id(payment_form_id: str, session: AsyncSession) -> PaymentFormResponseScheme:
    payment_form: PaymentFormModel | None = (await session.execute(
        select(PaymentFormModel)
        .where(PaymentFormModel.id == payment_form_id)
    )).scalars().first()

    if payment_form is None:
        raise HTTPException(status_code=404, detail="Payment form not found")

    external_transaction: ExternalTransactionModel | None = (await session.execute(
        select(ExternalTransactionModel)
        .where(ExternalTransactionModel.id == payment_form.id)
    )).scalars().first()

    if external_transaction is None:
        methods = list(map(lambda x: _prepare_method(x), payment_form.config))

        methods = await _filter_available_methods(session, payment_form.merchant_id, methods)

        return PaymentFormNewResponseScheme(
            id=payment_form.id,
            website_name=payment_form.merchant_website_name,
            create_timestamp=payment_form.create_timestamp,
            currency_name=payment_form.currency_name,
            auto_close_time=payment_form.auto_close_time,
            amount=payment_form.amount,
            return_url=payment_form.return_url,
            success_url=payment_form.success_url,
            fail_url=payment_form.fail_url,
            status=PaymentFormStatusEnum.NEW,
            methods=methods
        )

    if external_transaction.status in [Status.ACCEPT, Status.CLOSE]:
        return PaymentFormFinishResponseScheme(
            id=payment_form.id,
            website_name=payment_form.merchant_website_name,
            create_timestamp=external_transaction.create_timestamp,
            currency_name=payment_form.currency_name,
            auto_close_time=payment_form.auto_close_time,
            amount=payment_form.amount,
            return_url=payment_form.return_url,
            status=PaymentFormStatusEnum.FINISHED,
            transaction_status=external_transaction.status,
        )

    data = {
        "id": payment_form.id,
        "website_name": payment_form.merchant_website_name,
        "create_timestamp": external_transaction.create_timestamp,
        "currency_name": payment_form.currency_name,
        "amount": payment_form.amount,
        "auto_close_time": payment_form.auto_close_time,
        "return_url": payment_form.return_url,
        "success_url": payment_form.success_url,
        "fail_url": payment_form.fail_url,
        "status": PaymentFormStatusEnum.PENDING,
        "method": payment_form.method,
        "links": payment_form.links
    }

    if data["method"] == 'sberpay' or data["method"] == 't-pay':
        pass
    else:
        bank_detail: BankDetailModel | None = (await session.execute(
            select(BankDetailModel)
            .where(BankDetailModel.id == external_transaction.bank_detail_id)
        )).scalars().first()
        data["bank"] = ASSOCIATE_BANK.get(external_transaction.bank_detail_bank, external_transaction.bank_detail_bank)
        data["bank_number"] = external_transaction.bank_detail_number
        data["bank_name"] = external_transaction.bank_detail_name
        data["bank_icon_url"] = f'/v2/payment-form/bank-icon/{external_transaction.bank_detail_bank}'
        data["payment_system"] = bank_detail.payment_system

    return PaymentFormPendingResponseScheme(
        **data
    )


async def get_payment_form_status(payment_form_id: str):
    async with (ro_async_session() as session):
        payment_form: PaymentFormModel | None = (await session.execute(
            select(PaymentFormModel)
            .where(PaymentFormModel.id == payment_form_id)
        )).scalars().first()

        if payment_form is None:
            raise HTTPException(status_code=404, detail="Payment form not found")

        external_transaction: ExternalTransactionModel | None = (await session.execute(
            select(ExternalTransactionModel)
            .where(ExternalTransactionModel.id == payment_form_id)
        )).scalars().first()

        if external_transaction is None:
            return PaymentFormStatusEnum.NEW

        if external_transaction.status in [Status.ACCEPT, Status.CLOSE]:
            return PaymentFormStatusEnum.FINISHED

        return PaymentFormStatusEnum.PENDING


async def cancel(payment_form_id: str) -> PaymentFormResponseScheme:
    async with async_session() as session:
        payment_form: PaymentFormModel | None = (await session.execute(
            select(PaymentFormModel)
            .where(PaymentFormModel.id == payment_form_id)
        )).scalars().first()

        if payment_form is None:
            raise HTTPException(status_code=404, detail="Payment form not found")

        external_transaction: ExternalTransactionModel | None = (await session.execute(
            select(ExternalTransactionModel)
            .where(ExternalTransactionModel.id == payment_form_id)
        )).scalars().first()

        if external_transaction is None:
            return await get_by_id(payment_form_id, session)

        if external_transaction.status == Status.PENDING:
            await external_transaction_update_(
                transaction_id=external_transaction.id,
                session=session,
                status=Status.CLOSE,
                final_status=TransactionFinalStatusEnum.CANCEL
            )

        return await get_by_id(payment_form_id, session)


def get_bank_icon(bank: str) -> FileResponse:
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


def _get_method_by_name(array: List[PaymentFormConfigScheme], method_name: str) -> PaymentFormConfigScheme | None:
    for item in array:
        if item['name'] == method_name:
            return item

    return None


def _prepare_method(data) -> dict:
    name = data.get('name', '')
    options = data.get('options', {})
    types = options.get('types', None)
    banks = options.get('banks', None)

    return {
        'name': name,
        'types': types,
        'banks': banks
    }


async def _filter_available_methods(session: AsyncSession, merchant_id: str, methods: list):
    team_ids_subquery = (select(FeeContractModel.team_id)
                         .where(FeeContractModel.merchant_id == merchant_id))

    query = (select(BankDetailModel.bank, BankDetailModel.type)
             .where(
                BankDetailModel.is_active == True,
                BankDetailModel.team_id.in_(team_ids_subquery)
             )
             .distinct())

    unique_pairs = (await session.execute(query)).all()

    return list(map(lambda x: x['name'], filter(lambda x: _check_if_method_available(x, unique_pairs), methods)))


def _check_if_method_available(method_data, pairs):
    method_name = method_data['name']

    if method_name not in METHODS_REQUIREMENTS:
        return False

    method = METHODS_REQUIREMENTS[method_name]

    types = method_data['types'] or method['types']
    banks = method_data['banks'] or method['banks']

    return any(
        (not banks or pair[0] in banks) and
        (not types or pair[1] in types)
        for pair in pairs
    )
