from typing import Optional

from app.schemas.BaseScheme import BaseScheme
from app.schemas.UserScheme import UserMerchantScheme


class CreateMerchantRequestScheme(BaseScheme):
    name: str
    limit: int = 0
    rate_model: str
    geo_id: int
    balance_id: str | None = None


class UpdateMerchantRequestScheme(BaseScheme):
    is_outbound_enabled: bool | None = None
    is_inbound_enabled: bool | None = None
    currency_id: str | None = None
    credit_factor: int | None = None
    is_blocked: bool | None = None
    transaction_auto_close_time_s: int | None = None
    transaction_outbound_auto_close_time_s: int | None = None
    left_eps_change_amount_allowed: int | None = None
    right_eps_change_amount_allowed: int | None = None
    min_fiat_amount_in: int | None = None
    max_fiat_amount_in: int | None = None


class MerchantResponseScheme(BaseScheme):
    id: str
    balance_id: str
    name: str
    pay_in: int
    pay_out: int
    is_inbound_enabled: bool = False
    is_outbound_enabled: bool = False
    transaction_auto_close_time_s: int = 0
    transaction_outbound_auto_close_time_s: int = 0
    trust_balance: int = 0
    profit_balance: int = 0
    locked_balance: int = 0
    fiat_trust_balance: int = 0
    fiat_locked_balance: int = 0
    fiat_profit_balance: int = 0
    credit_factor: int
    telegram_verifier_chat_id: str | None = None
    rate_model: str | None = None
    is_blocked: bool
    password: str | None = None
    api_secret: str | None = None


class V2MerchantResponseScheme(UserMerchantScheme):
    pay_in: int
    pay_out: int
    trust_balance: int = 0
    profit_balance: int = 0
    locked_balance: int = 0
    fiat_trust_balance: int = 0
    fiat_locked_balance: int = 0
    fiat_profit_balance: int = 0
    password: Optional[str] = None
    api_secret: Optional[str] = None
