import datetime
from typing import List, Tuple
from app.schemas.BaseScheme import BaseScheme, str_big_factory, str_small_factory, num_factory


# --------------------------------------------CREATE-----------------------------------------------
class BankDetailSchemeRequestCreateBase(BaseScheme):
    name: str | None = str_big_factory(None)
    bank: str | None = str_small_factory(None)
    alias: str | None = str_small_factory(None)
    payment_system: str | None = str_small_factory(None)
    type: str | None = str_small_factory(None)
    number: str | None = str_small_factory(None)
    second_number: str | None = str_small_factory(None)
    is_active: bool | None = None
    is_vip: bool | None = None
    max_vip_payers: int | None = num_factory(None)
    amount_limit: int | None = num_factory(None)
    device_hash: str | None = str_small_factory(None)
    comment: str | None = str_big_factory(None)
    #transactions_count_limit: List[Tuple[str, str, int, int]] | None = None
    auto_managed: bool | None = None
    fiat_max_inbound: int | None = num_factory(None)
    fiat_min_inbound: int | None = num_factory(None)
    max_today_amount_used: int | None = num_factory(None)
    max_pending_count: int | None = num_factory(None)
    max_today_transactions_count: int | None = num_factory(None)
    period_start_time: datetime.time | None = None
    period_finish_time: datetime.time | None = None
    period_time: List[int] | None = None
    delay: int | None = None
    profile_id: str | None = None


class BankDetailSchemeRequestCreate(BankDetailSchemeRequestCreateBase):
    pass


class BankDetailSchemeRequestCreateDB(BankDetailSchemeRequestCreateBase):
    team_id: str = str_small_factory()


class BankDetailSchemeResponse(BankDetailSchemeRequestCreateDB):
    id: str = str_small_factory()
    create_timestamp: datetime.datetime
    is_deleted: bool
    amount_used: int = num_factory()
    offset_id: int = num_factory()
    last_transaction_timestamp: datetime.datetime
    today_transactions_count: int = num_factory()
    today_amount_used: int = num_factory()
    count_vip_payers: int = num_factory()


# --------------------------------------------LIST-------------------------------------------------
class BankDetailSchemeRequestList(BaseScheme):
    search: str | None = str_small_factory()
    bank: str | None = str_small_factory()
    payment_system: str | None = str_small_factory()
    is_active: bool | None
    is_vip: bool | None
    last_offset_id: int = num_factory()
    limit: int = num_factory()


class BankDetailSchemeRequestListDB(BankDetailSchemeRequestList):
    team_id: str = str_small_factory()


class BankDetailSchemeResponseList(BaseScheme):
    items: List[BankDetailSchemeResponse]


class BankDetailProfilesResponse(BaseScheme):
    profile_id: str | None
    name: str | None


class BankDetailStatisticSchemeResponse(BaseScheme):
    id: str
    count_transactions: int
    count_transactions_day: int
    average_amount: int
    average_amount_day: int
    average_profit: int
    average_profit_day: int
    sum_profit: int
    sum_profit_day: int
    average_fee: float | None
    average_fee_day: float | None
    conversion: int | None
    conversion_day: int | None


class BankDetailProfilesResponseList(BaseScheme):
    items: List[BankDetailProfilesResponse]


# --------------------------------------------DELETE------------------------------------------------
class BankDetailSchemeRequestDelete(BaseScheme):
    id: str = str_small_factory()


class BankDetailSchemeRequestDeleteDB(BankDetailSchemeRequestDelete):
    team_id: str = str_small_factory()


# -------------------------------------------------UPDATE-------------------------------------------
class UpdateBankDetailResponse(BaseScheme):
    name: str | None = str_big_factory(None)
    bank: str | None = str_small_factory(None)
    alias: str | None = str_small_factory(None)
    type: str | None = str_small_factory(None)
    payment_system: str | None = str_small_factory(None)
    number: str | None = str_small_factory(None)
    second_number: str | None = str_small_factory(None)
    is_active: bool | None = None
    amount_limit: int | None = num_factory(None)
    device_hash: str | None = str_small_factory(None)
    comment: str | None = str_big_factory(None)
    fiat_max_inbound: int | None = num_factory(None)
    fiat_min_inbound: int | None = num_factory(None)
    last_transaction_timestamp: datetime.datetime | None
    today_amount_used: int | None = num_factory(None)
    max_today_amount_used: int | None = num_factory(None)
    max_pending_count: int | None = num_factory(None)
    is_vip: bool | None = None
    max_vip_payers: int | None = num_factory(None)
    count_vip_payers: int | None = num_factory(None)
    profile_id: str | None = str_big_factory(None)


class BankDetailSchemeResponseUpdateID(BankDetailSchemeRequestCreateBase):
    pass


class BankDetailSchemeRequestUpdate(BankDetailSchemeResponseUpdateID):
    id: str = str_small_factory()


class BankDetailSchemeRequestUpdateDB(BankDetailSchemeRequestUpdate):
    team_id: str = str_small_factory()
