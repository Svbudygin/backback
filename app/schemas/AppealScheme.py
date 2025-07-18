from typing import List, Optional, Union
from enum import Enum
from datetime import datetime
from pydantic import ConfigDict
from decimal import Decimal
from app.schemas.BaseScheme import (
    BaseScheme
)
from app.core.constants import StatusEnum


class AppealStatusEnum(Enum):
    pending = 'pending'
    wait_team_statement = 'wait_team_statement'
    wait_merchant_statement = 'wait_merchant_statement'
    wait_statement = 'wait statement'
    accept = 'accept'
    close = 'close'


class AppealCloseCodeEnum(Enum):
    incorrect_reqs = 'INCORRECT_REQS'
    fake_receipt = 'FAKE_RECEIPT'
    closed_another_transaction = 'CLOSED_ANOTHER_TRANSACTION'
    timeout = 'TIMEOUT'


class PartialTeamScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    name: str


class PartialMerchantScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    name: str
    geo_id: Optional[int]


class PartialBankDetailScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    alias: Optional[str] = None


class PartialTransactionScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_transaction_id: Optional[str] = None
    status: StatusEnum
    create_timestamp: datetime
    type: Optional[str] = None
    bank_detail_bank: Optional[str] = None
    bank_detail_number: Optional[str] = None
    bank_detail_name: Optional[str] = None
    bank_detail: Optional[PartialBankDetailScheme] = None
    amount: int
    close_timestamp: Optional[datetime] = None
    currency_id: str

    team: Optional[PartialTeamScheme] = None


class PartialFullTransactionScheme(PartialTransactionScheme):
    merchant: Optional[PartialMerchantScheme] = None


class AppealScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: str
    create_timestamp: datetime
    update_timestamp: datetime
    close_timestamp: Optional[datetime] = None
    offset_id: int

    transaction_id: str
    transaction: Optional['PartialFullTransactionScheme']

    merchant_appeal_id: Optional[str] = None
    finalization_callback_uri: Optional[str] = None
    ask_statement_callback_uri: Optional[str] = None

    amount: Optional[int]
    receipts: Optional[List[str]]
    merchant_statements:  Optional[List[str]]
    team_statements: Optional[List[str]]

    is_merchant_statement_required: bool
    is_team_statement_required: bool
    is_support_confirmation_required: bool

    reject_reason: Optional[str]
    reject_comment: Optional[str]
    team_processing_start_time: Optional[datetime]


class AppealCreateScheme(BaseScheme):
    transaction_id: str
    merchant_appeal_id: Optional[str] = None
    finalization_callback_uri: Optional[str] = None
    ask_statement_callback_uri: Optional[str] = None
    amount: Optional[int] = None


class AppealBaseResponseScheme(BaseScheme):
    model_config = ConfigDict(
        from_attributes=True,
        extra='ignore'
    )

    id: str
    status: AppealStatusEnum
    create_timestamp: datetime
    close_timestamp: Optional[datetime] = None
    new_amount: Optional[int] = None


class AppealMerchantResponseScheme(AppealBaseResponseScheme):
    merchant_appeal_id: Optional[str] = None
    merchant_transaction_id: Optional[str] = None
    code: Optional[str] = None
    comment: Optional[str] = None


class AppealTeamResponseScheme(AppealBaseResponseScheme):
    transaction: PartialTransactionScheme
    merchant_statements: Optional[list[str]] = None
    team_statements: Optional[list[str]] = None
    reject_reason: Optional[str] = None
    reject_comment: Optional[str] = None
    offset_id: int
    auto_accept_timestamp: Optional[datetime] = None


class AppealSupportResponseScheme(AppealBaseResponseScheme):
    transaction: PartialFullTransactionScheme
    merchant_statements: Optional[list[str]] = None
    team_statements: Optional[list[str]] = None
    reject_reason: Optional[str] = None
    reject_comment: Optional[str] = None
    offset_id: int
    auto_accept_timestamp: Optional[datetime] = None


AppealResponseScheme = Union[
    AppealMerchantResponseScheme,
    AppealTeamResponseScheme,
    AppealSupportResponseScheme
]


class AppealUpdateBaseScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)


class AppealMerchantUpdateScheme(AppealUpdateBaseScheme):
    amount: Optional[int] = None


class AppealSupportUpdateScheme(AppealUpdateBaseScheme):
    amount: Optional[int] = None
    reject_reason: Optional[str] = None
    reject_comment: Optional[str] = None


class AppealTeamUpdateScheme(AppealUpdateBaseScheme):
    amount: Optional[int] = None


AppealUpdateScheme = Union[
    AppealMerchantUpdateScheme,
    AppealSupportUpdateScheme,
    AppealTeamUpdateScheme
]


class AppealListFilterScheme(BaseScheme):
    direction: Optional[str] = None
    status: Optional[str] = None
    from_timestamp: Optional[datetime] = None
    to_timestamp: Optional[datetime] = None
    geo_id: Optional[int] = None
    search: Optional[str] = None
    team_id: Optional[str] = None
    merchant_id: Optional[str] = None


class CancelAppealRequestScheme(BaseScheme):
    reason: str


class AcceptAppealRequestScheme(BaseScheme):
    new_amount: Optional[int] = None


class NewSupportConfirmationRequiredSchema(BaseModel):
    appeal_id: str
    transaction_id: str
    merchant_transaction_id: Optional[str] = None
    merchant_appeal_id: Optional[str] = None

    # заполняется, если команда изменила сумму
    new_amount: Optional[Decimal] = None

    # заполняется, если команда отклонила апелляцию
    reject_reason: Optional[str] = None

