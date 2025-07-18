from typing import Optional, List

from app.schemas.BaseScheme import (
    BaseScheme,
    str_small_factory,
    num_factory
)

class ResponseAccountingScheme(BaseScheme):
    id: str = str_small_factory()
    offset_id: str = str_small_factory()
    role: str = str_small_factory()
    name: str = str_small_factory()
    geo: str | None = str_small_factory(None)
    balance: float = num_factory()
    pending_deposit: float = num_factory()
    pending_withdraw: float = num_factory()

class ListResponseAccounting(BaseScheme):
    items: List[ResponseAccountingScheme]

class FilterAccountingScheme(BaseScheme):
    last_offset_id: int | None = num_factory(None)
    limit: int | None = num_factory(None)
    role: str | None = str_small_factory(None)
    geo_id: int | None = num_factory(None)
    search: str | None = str_small_factory(None)

class DownloadAccountingScheme(BaseScheme):
    create_timestamp_from: int | None = num_factory(None)
    create_timestamp_to: int | None = num_factory(None)
