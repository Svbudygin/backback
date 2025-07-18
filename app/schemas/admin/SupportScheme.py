from typing import Optional

from app.schemas.BaseScheme import BaseScheme
from app.schemas.UserScheme import UserSupportScheme


class CreateSupportRequestScheme(BaseScheme):
    name: str
    view_traffic: bool | None = None
    view_fee: bool | None = None
    view_pay_in: bool | None = None
    view_pay_out: bool | None = None
    view_teams: bool | None = None
    view_merchants: bool | None = None
    view_agents: bool | None = None
    view_wallet: bool | None = None
    view_supports: bool | None = None
    view_search: bool | None = None
    view_compensations: bool | None = None
    view_sms_hub: bool | None = None
    view_accounting: bool | None = None
    view_details: bool | None = None
    view_appeals: bool | None = None
    view_analytics: bool | None = None
    is_blocked: bool | None = None


class UpdateSupportRequestScheme(BaseScheme):
    is_blocked: bool = None
    view_traffic: bool = None
    view_fee: bool = None
    view_pay_in: bool = None
    view_pay_out: bool = None
    view_teams: bool = None
    view_merchants: bool = None
    view_agents: bool = None
    view_wallet: bool = None
    view_supports: bool = None
    view_search: bool = None
    view_compensations: bool = None
    view_sms_hub: bool | None = None
    view_accounting: bool | None = None
    view_details: bool | None = None
    view_appeals: bool | None = None
    view_analytics: bool | None = None


class SupportResponseScheme(BaseScheme):
    id: str
    name: str
    view_traffic: bool | None = None
    view_fee: bool | None = None
    view_pay_in: bool | None = None
    view_pay_out: bool | None = None
    view_teams: bool | None = None
    view_merchants: bool | None = None
    view_agents: bool | None = None
    view_wallet: bool | None = None
    view_supports: bool | None = None
    view_search: bool | None = None
    view_compensations: bool | None = None
    view_sms_hub: bool | None = None
    view_accounting: bool | None = None
    view_details: bool | None = None
    view_appeals: bool | None = None
    is_blocked: bool | None = None
    password: str | None = None


class V2SupportResponseScheme(UserSupportScheme):
    view_traffic: bool | None = None
    view_fee: bool | None = None
    view_pay_in: bool | None = None
    view_pay_out: bool | None = None
    view_teams: bool | None = None
    view_merchants: bool | None = None
    view_agents: bool | None = None
    view_wallet: bool | None = None
    view_supports: bool | None = None
    view_search: bool | None = None
    view_compensations: bool | None = None
    view_sms_hub: bool | None = None
    view_accounting: bool | None = None
    view_details: bool | None = None
    view_appeals: bool | None = None
    view_analytics: bool | None = None
    password: Optional[str] = None
