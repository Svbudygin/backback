from datetime import datetime
from pydantic import ConfigDict, field_validator
from typing import Optional, Union, List

from app.core.constants import DECIMALS
from app.schemas.BaseScheme import (
    BaseScheme,
    num_factory,
    str_big_factory,
    str_small_factory,
)

class MessageRequestScheme(BaseScheme):
    last_offset_id: int = num_factory()
    limit: int = num_factory()
    timestamp_from: int | None = num_factory(None)
    timestamp_to: int | None = num_factory(None)
    user_id: str | None = str_small_factory(None)
    search: str | None = str_small_factory(None)
    geo_id: int | None = num_factory(None)
    bank: str | None = str_small_factory(None)
    status: bool | None = None

class Response(BaseScheme):
    offset_id: int | None = num_factory(None)
    id: str | None = str_small_factory(None)
    number: str | None = str_small_factory(None)
    alias: str | None = str_small_factory(None)
    user_id: str | None = str_small_factory(None)
    team_name: str | None = str_small_factory(None)
    create_timestamp: datetime | None = None
    text: str | None = str_big_factory(None)
    title: str | None = str_big_factory(None)
    device_hash: str | None = str_small_factory(None)
    external_transaction_id: str | None = str_small_factory(None)
    bank_detail_number: str | None = str_small_factory(None)
    type: str | None = str_small_factory(None)

class ListResponse(BaseScheme):
    items: List[Response]