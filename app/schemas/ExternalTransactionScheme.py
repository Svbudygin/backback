from datetime import datetime
from typing import List, Optional

from app.core.constants import Limit, ReasonName
from app.schemas.BaseScheme import (
    BaseScheme,
    num_factory,
    str_big_factory,
    str_small_factory,
)
from app.enums import TransactionFinalStatusEnum


class BankDetailResponse(BaseScheme):
    id: str = str_small_factory()
    name: str | None = str_big_factory()
    bank: str | None = str_small_factory()
    type: str = str_small_factory()
    payment_system: str | None = str_small_factory()
    number: str = str_small_factory()
    second_number: str | None = str_small_factory(None)
    bank_icon_url: str | None = None


class ResponseInboundGetTeamBankDetail(BaseScheme):
    team_id: str = str_small_factory()
    bank_detail: BankDetailResponse
    currency_id: str = str_small_factory()


class ResponseOutboundGetTeamBankDetail(BaseScheme):
    team_id: str = str_small_factory()
    currency_id: str = str_small_factory()


class RequestCreate(BaseScheme):
    amount: int = num_factory()
    direction: str = str_small_factory()
    bank_detail_id: str | None = str_small_factory()
    bank_detail_number: str = str_small_factory()
    bank_detail_bank: str | None = str_small_factory(None)
    type: str | None = str_small_factory(None)
    bank_detail_name: str | None = str_big_factory(None)
    economic_model: str | None = (str_small_factory(None),)

    team_id: str | None = str_small_factory()
    hook_uri: str | None = str_big_factory()
    merchant_transaction_id: str | None = str_small_factory()
    additional_info: str | None = str_small_factory()
    currency_id: str = str_small_factory()
    merchant_payer_id: str | None = str_small_factory()
    tag_code: str | None = str_small_factory(None)


class AmountStatusResponse(BaseScheme):
    amount: float = num_factory()
    status: str = str_small_factory()


class RequestCreateDB(RequestCreate):
    merchant_id: str = str_small_factory()
    status: str = str_small_factory()
    merchant_payer_id: str | None = str_small_factory()


class RequestGetBankDetailDB(BaseScheme):
    amount: int | None = num_factory()
    merchant_id: str = str_small_factory()
    is_inbound: bool
    currency_id: str = str_small_factory()
    type: str | None = str_small_factory()


class Response(RequestCreate):
    id: str
    create_timestamp: datetime
    transfer_to_team_timestamp: datetime | None = None
    status: str
    is_approved: bool
    exchange_rate: int
    file_uri: str | None
    offset_id: int
    bank_detail_number: str | None = str_small_factory(None)
    bank_detail_bank: str | None = str_small_factory(None)
    type: str | None = str_small_factory(None)
    bank_detail_name: str | None = str_big_factory(None)
    transaction_auto_close_time_s: int | None = num_factory(None)
    transaction_outbound_auto_close_time_s: int | None = num_factory(None)
    merchant_name: str | None = str_small_factory(None)
    team_name: str | None = str_small_factory(None)
    tag_id: str | None = str_small_factory(None)
    text: str | None = str_big_factory(None)
    reason: str | None = str_small_factory(None)
    comment: str | None =  str_small_factory(None)
    alias: str | None =  str_small_factory(None)
    priority: int | None = num_factory(None)
    final_status_timestamp: datetime | None = None
    count_hold: int
    auto_close_outbound_transactions_s: int | None = None
    final_status: Optional[TransactionFinalStatusEnum] = None


class PaymentFormResponse(BaseScheme):
    amount: int = num_factory()
    currency_id: str = str_small_factory()
    id: str
    create_timestamp: datetime
    status: str
    bank_detail_number: str
    bank_detail_bank: str
    bank_detail_name: str
    bank_icon_url: str | None = str_big_factory()
    transaction_auto_close_time_s: int


class RequestList(BaseScheme):
    last_priority: int = num_factory()
    limit: int = num_factory()
    user_id: str = str_small_factory()
    role: str = str_small_factory()
    search: str | None = str_small_factory()
    geo_id: int | None = num_factory()
    type: str | None = str_small_factory()
    bank: str | None = str_small_factory()
    direction: str | None = (str_small_factory(),)
    status: str | None = (str_small_factory(),)
    amount_from: int | None = num_factory()
    amount_to: int | None = num_factory()
    currency_id: str | None = (str_small_factory(),)
    create_timestamp_from: int | None = (None,)
    create_timestamp_to: int | None = None
    merchant_id: str | None = str_small_factory(None)
    team_id: str | None = str_small_factory(None)
    final_status: Optional[TransactionFinalStatusEnum] = None


class ResponseList(BaseScheme):
    items: List[Response]


class RequestUpdateStatus(BaseScheme):
    merchant_transaction_id: str | None = str_small_factory(None)
    transaction_id: str | None = str_small_factory(None)
    status: str | None = str_small_factory()
    new_amount: int | None = num_factory(None)
    reason: ReasonName | None = None
    final_status: TransactionFinalStatusEnum | None = None


class RequestTransfer(BaseScheme):
    transaction_id: str | None = str_small_factory()


class RequestTransferToTeam(BaseScheme):
    team_id: str


class RequestUpdateStatusDB(RequestUpdateStatus):
    tag_code: str | None = None


class RequestUpdateFile(BaseScheme):
    transaction_id: str = str_small_factory()


class RequestUpdateFileDB(RequestUpdateFile):
    team_id: str = str_small_factory()
    file_uri: str = str_big_factory()


class RequestUpdateFromDeviceDB(BaseScheme):
    message: str = str_big_factory()
    package_name: str | None = str_small_factory(None)
    api_secret: str = str_small_factory()
    device_hash: str | None = str_small_factory(None)
    bank: str | None = str_big_factory()
    timestamp: int | None = None


class Message(BaseScheme):
    title: str = str_big_factory()
    extra_text: str = str_big_factory(
        max_length=Limit.MAX_STRING_LENGTH_BIG
    )
    package_name: str | None = str_small_factory(None)
    timestamp: int | None = None


class RequestUpdateFromDevice(BaseScheme):
    api_secret: str = str_small_factory()
    message: Message
    device_hash: str | None = str_small_factory()


class RequestCheckDeviceToken(BaseScheme):
    api_secret: str = str_small_factory()


class ResponseCheckDeviceToken(BaseScheme):
    team_name: str = str_small_factory()


class RequestCreatePayment(BaseScheme):
    type: str | None = str_small_factory()


class RequestCreatePaymentOutbound(BaseScheme):
    type: str | None = str_small_factory()
    bank_detail_number: str = str_small_factory()
    bank_detail_bank: str | None = str_small_factory(None)
    bank_detail_name: str | None = str_small_factory(None)


class StatusResponse(BaseScheme):
    status: str = str_small_factory()


class ExportTransactionsRequest(BaseScheme):
    user_id: str
    status: str | None = str_small_factory()
    direction: str | None = str_small_factory()
    role: str = str_small_factory()
    amount_from: int | None = num_factory()
    amount_to: int | None = num_factory()
    currency_id: str | None = str_small_factory()
    create_timestamp_from: int | None = None
    create_timestamp_to: int | None = None


class ExportTransactionsResponse(BaseScheme):
    transaction_id: str
    merchant_transaction_id: str
    create_timestamp: datetime
    direction: str
    bank_detail_number: str
    transaction_amount: float
    status: str
    exchange_rate: float
    usdt_deposit_change: int | float | None = None
    interest: float | None = 0


class ExportSumTransactionsResponse(BaseScheme):
    token_name: str | None = None
    team_name: str | None = None
    transaction_id: str | None = None
    merchant_transaction_id: str | None = None
    merchant_payer_id: str | None = None
    create_timestamp: datetime | None = None
    direction: str | None = None
    bank_detail_number: str | None = None
    transaction_amount: float | None = None
    status_last_update_timestamp: datetime | None = None
    status: str | None = None
    exchange_rate: float | None = None
    usdt_deposit_change: float | None = 0
    interest: float | None = 0
    cumulative_trust_balance: float | None = 0


class FileBase64(BaseScheme):
    name: str
    file: str

class DeclineRequest(BaseScheme):
    transaction_id: str
    reason: ReasonName
    files: List[FileBase64]