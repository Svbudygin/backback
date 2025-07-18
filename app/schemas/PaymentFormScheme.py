from datetime import datetime

from typing import Optional, List, Union, Literal
from enum import Enum

from app.schemas.BaseScheme import (
    BaseScheme,
)

# TODO: change bank and type to enums


class PaymentFormStatusEnum(str, Enum):
    NEW = 'new',
    PENDING = 'pending',
    FINISHED = 'finished',


class FinalTransactionStatusEnum(str, Enum):
    ACCEPT = 'accept',
    CLOSE = 'close'


class PaymentFormConfigOptionsScheme(BaseScheme):
    types: Optional[List[str]] = None
    banks: Optional[List[str]] = None
    payment_systems: Optional[List[str]] = None
    tag_code: Optional[str] = None
    is_vip: bool = False


class PaymentFormConfigScheme(BaseScheme):
    name: str
    options: Optional[PaymentFormConfigOptionsScheme] = None


class PaymentFormScheme(BaseScheme):
    id: str
    merchant_transaction_id: str
    hook_uri: Optional[str] = None
    payer_id: str
    merchant_id: str
    amount: int
    return_url: Optional[str] = None
    success_url: Optional[str] = None
    fail_url: Optional[str] = None
    merchant_website_name: Optional[str] = None
    method: Optional[str] = None
    links: Optional[dict] = None
    currency_name: str
    auto_close_time: int
    config: List[PaymentFormConfigScheme]

    class Config:
        from_attributes = True


class CreatePaymentFormScheme(BaseScheme):
    api_secret: str
    merchant_transaction_id: str
    hook_uri: Optional[str] = None
    payer_id: str
    amount: int
    return_url: Optional[str] = None
    success_url: Optional[str] = None
    fail_url: Optional[str] = None
    merchant_website_name: Optional[str] = None
    config: List[PaymentFormConfigScheme]

    class Config:
        from_attributes = True


class BasePaymentFormResponseScheme(BaseScheme):
    id: str
    website_name: Optional[str] = None
    amount: int
    create_timestamp: datetime
    auto_close_time: int
    return_url: Optional[str] = None
    success_url: Optional[str] = None
    fail_url: Optional[str] = None
    currency_name: str
    status: PaymentFormStatusEnum

    class Config:
        from_attributes = True


class PaymentFormNewResponseScheme(BasePaymentFormResponseScheme):
    status: Literal[PaymentFormStatusEnum.NEW] = PaymentFormStatusEnum.NEW
    methods: List[str] = []


class PaymentFormPendingResponseScheme(BasePaymentFormResponseScheme):
    status: PaymentFormStatusEnum = PaymentFormStatusEnum.PENDING
    method: str
    links: Optional[dict] = None

    # Sberpay
    link: Optional[str] = None

    # Other
    bank: Optional[str] = None
    bank_name: Optional[str] = None
    bank_number: Optional[str] = None
    bank_icon_url: Optional[str] = None
    payment_system: Optional[str] = None

class PaymentFormFinishResponseScheme(BasePaymentFormResponseScheme):
    status: PaymentFormStatusEnum = PaymentFormStatusEnum.FINISHED
    transaction_status: FinalTransactionStatusEnum


PaymentFormResponseScheme = Union[
    PaymentFormNewResponseScheme,
    PaymentFormPendingResponseScheme,
    PaymentFormFinishResponseScheme
]
