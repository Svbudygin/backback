from datetime import datetime

from app.schemas.BaseScheme import BaseScheme


class TrafficWeightScheme(BaseScheme):
    id: str | None = None
    merchant_id: str | None = None
    team_id: str | None = None
    type: str | None = None
    inbound_traffic_weight: int | None = None
    is_outbound_traffic: bool | None = None
    outbound_amount_less_or_eq: int | None = None
    outbound_amount_great_or_eq: int | None = None
    outbound_bank_in: list[str] | None = None
    outbound_bank_not_in: list[str] | None = None
    create_timestamp: datetime | None = None
    team_name: str | None = None
    trust_balance: int | None = None
    locked_balance: int | None = None
    credit_factor: int | None = None
    stats: dict | None = None
