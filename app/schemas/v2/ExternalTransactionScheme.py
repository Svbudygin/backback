from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.BaseScheme import BaseScheme, str_small_factory, num_factory, str_big_factory
from app.schemas.ExternalTransactionScheme import BankDetailResponse
from app.schemas.admin.TagScheme import TagScheme


class H2HCreateBase(BaseModel):
    amount: int = num_factory()
    hook_uri: str | None = str_big_factory(None)
    type: Optional[str] = str_small_factory(None)
    tag_code: str | None = str_small_factory(None)
    bank: str | None = str_small_factory(None)
    banks: Optional[List[str]] = None
    types: Optional[List[str]] = None

class H2HCreateInboundJWT(H2HCreateBase):
    is_vip: bool = False
    payment_systems: Optional[List[str]] = None
    merchant_payer_id: str = str_small_factory()
    merchant_transaction_id: str = str_small_factory()


class H2HCreateOutboundJWT(H2HCreateBase):
    bank_detail_number: str = str_small_factory()
    bank_detail_bank: str | None = str_small_factory(None)
    bank_detail_name: str | None = str_small_factory(None)
    
    merchant_payer_id: str = str_small_factory()
    merchant_transaction_id: str = str_small_factory()


class H2HCreateInbound(H2HCreateBase):
    is_vip: bool = False
    payment_systems: Optional[List[str]] = None
    merchant_id: str = str_small_factory()
    merchant_payer_id: str = str_small_factory()
    merchant_transaction_id: str = str_small_factory()


class H2HCreateOutbound(H2HCreateBase):
    currency_id: str | None = str_small_factory(None)
    bank_detail_number: str = str_small_factory()
    bank_detail_bank: str | None = str_small_factory(None)
    bank_detail_name: str | None = str_small_factory(None)
    
    merchant_id: str = str_small_factory()
    merchant_payer_id: str = str_small_factory()
    merchant_transaction_id: str = str_small_factory()


class H2HInboundResponse(BaseModel):
    id: str = str_small_factory()
    direction: str = str_small_factory()
    amount: int = num_factory()
    currency_id: str = str_small_factory()
    exchange_rate: int | None = num_factory(None)
    status: str = str_small_factory()
    create_timestamp: datetime
    bank_detail: BankDetailResponse
    tag_id: str | None = None
    payment_link: dict | None = None
    transaction_auto_close_time_s: int


class H2HOutboundResponse(BaseModel):
    id: str = str_small_factory()
    direction: str = str_small_factory()
    amount: int = num_factory()
    currency_id: str = str_small_factory()
    status: str = str_small_factory()
    exchange_rate: int | None = num_factory(None)
    create_timestamp: datetime
    tag_id: str | None = None


class H2HGetRequest(BaseModel):
    merchant_id: str | None = str_small_factory()
    id: str | None = str_small_factory(),
    merchant_transaction_id: str | None = str_small_factory()


class H2HGetResponse(BaseModel):
    id: str = str_small_factory()
    merchant_transaction_id: str | None = str_small_factory()
    direction: str
    amount: int = num_factory()
    status: str = str_small_factory()
    merchant_trust_change: int = num_factory(0)
    create_timestamp: datetime
    tag_id: str | None = None
    currency_id: str | None = None
    exchange_rate: int | None = num_factory(None)


class GetOutboundRequest(BaseModel):
    amount_from: int | None = num_factory(None)
    amount_to: int | None = num_factory(None)
    external_transaction_id: str | None = str_small_factory(None)
    banks: list[str | None] | None = str_small_factory(None)
    tags: list[str | None] | None = str_small_factory(None)


class GetOutboundRequestDB(GetOutboundRequest):
    team_id: str


class GetOutboundFiltersResponse(BaseScheme):
    banks: list[str | None] | None = None
    tags: list[TagScheme] | None = None


class BalanceResponse(BaseScheme):
    balance: int = num_factory(0)


class BalancesResponse(BalanceResponse):
    locked_balance: int = num_factory(0)
