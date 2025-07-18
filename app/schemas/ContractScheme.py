from datetime import datetime
from typing import List

from app.schemas.BaseScheme import (
    BaseScheme,
    str_small_factory,
    str_big_factory,
    num_factory
)


# --------------------------------------------CREATE-----------------------------------------------

class RequestCreate(BaseScheme):
    merchant_id: str = str_small_factory()
    team_id: str = str_small_factory()
    comment: str | None = str_big_factory()


class FeeRequestCreate(RequestCreate):
    user_id: str = str_small_factory()
    inbound_fee: int = num_factory()
    outbound_fee: int = num_factory()
    tag_id: str | None = str_small_factory(None)


class TrafficWeightRequestCreate(RequestCreate):
    inbound_traffic_weight: int = num_factory()
    outbound_traffic_weight: int = num_factory()
    currency_id: str = str_small_factory()


class Response(RequestCreate):
    id: str = str_small_factory()
    is_deleted: bool
    offset_id: int = num_factory()
    create_timestamp: datetime


class TrafficWeightResponse(Response):
    inbound_traffic_weight: int = num_factory()
    outbound_traffic_weight: int = num_factory()
    currency_id: str = str_small_factory()


class FeeResponse(Response):
    inbound_fee: int = num_factory()
    outbound_fee: int = num_factory()
    tag_id: str | None = None


# --------------------------------------------LIST-------------------------------------------------
class RequestList(BaseScheme):
    last_offset_id: int = num_factory()
    limit: int = num_factory()


class FeeResponseList(BaseScheme):
    items: List[FeeResponse]


class TrafficWeightResponseList(BaseScheme):
    items: List[TrafficWeightResponse]


# --------------------------------------------DELETE------------------------------------------------
class RequestDelete(BaseScheme):
    id: str = str_small_factory()


# -------------------------------------------------UPDATE-------------------------------------------
class RequestUpdate(BaseScheme):
    id: str = str_small_factory()
    merchant_id: str | None = str_small_factory()
    team_id: str | None = str_small_factory()
    
    comment: str | None = str_big_factory()


class FeeRequestUpdate(RequestUpdate):
    user_id: str | None = str_small_factory()
    inbound_fee: int | None = num_factory()
    outbound_fee: int | None = num_factory()
    tag_id: str | None = None


class TrafficWeightRequestUpdate(RequestUpdate):
    inbound_traffic_weight: int | None = num_factory()
    outbound_traffic_weight: int | None = num_factory()
    currency_id: str = str_small_factory()
