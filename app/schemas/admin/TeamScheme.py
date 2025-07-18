from typing import Optional

from app.schemas.BaseScheme import BaseScheme
from app.schemas.UserScheme import UserTeamScheme


class InfoBalanceScheme(BaseScheme):
    name: str
    balance_id: str


class CreateTeamRequestScheme(BaseScheme):
    name: str
    geo_id: int
    limit: int = 0
    balance_id: str | None = None


class UpdateTeamRequestScheme(BaseScheme):
    is_outbound_enabled: bool | None = None
    is_inbound_enabled: bool | None = None
    credit_factor: int | None = None
    is_blocked: bool = None
    fiat_max_inbound: int | None = None
    fiat_min_inbound: int | None = None
    priority_inbound: int | None = None
    fiat_max_outbound: int | None = None
    fiat_min_outbound: int | None = None
    max_today_outbound_amount_used: int | None = None
    max_outbound_pending_per_token: int | None = None
    max_inbound_pending_per_token: int | None = None


class TeamResponseScheme(BaseScheme):
    id: str
    balance_id: str
    name: str
    pay_in: int
    pay_out: int
    is_inbound_enabled: bool = False
    is_outbound_enabled: bool = False
    trust_balance: int = 0
    profit_balance: int = 0
    locked_balance: int = 0
    fiat_trust_balance: int = 0
    fiat_locked_balance: int = 0
    fiat_profit_balance: int = 0
    credit_factor: int
    rate_model: str | None = None
    is_blocked: bool
    password: str | None = None
    api_secret: str | None = None
    fiat_max_inbound: int | None = None
    fiat_min_inbound: int | None = None
    priority_inbound: int | None = None
    max_outbound_pending_per_token: int | None = None
    max_inbound_pending_per_token: int | None = None


class V2TeamResponseScheme(UserTeamScheme):
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
