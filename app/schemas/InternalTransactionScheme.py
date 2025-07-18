from datetime import datetime
from typing import List, Optional

from app.schemas.BaseScheme import (
    BaseScheme,
    str_small_factory,
    num_factory
)


class InboundRequestCreateOpen(BaseScheme):
    amount: int = num_factory()


class InboundRequestCreateOpenDB(InboundRequestCreateOpen):
    user_id: str = str_small_factory()


class OutboundRequestCreateOpen(InboundRequestCreateOpen):
    amount: int = num_factory()
    address: str = str_small_factory()


class OutboundRequestCreateOpenDB(OutboundRequestCreateOpen):
    user_id: str = str_small_factory()
    is_autowithdraw_enabled: Optional[bool] = None


class Response(BaseScheme):
    id: str = str_small_factory()
    create_timestamp: datetime
    status: str = str_small_factory()
    blockchain_transaction_hash: str | None = str_small_factory(None)
    amount: int = num_factory()
    direction: str = str_small_factory()
    user_id: str = str_small_factory()
    from_address: str | None = str_small_factory(None)
    address: str | None = str_small_factory()
    
    offset_id: int = num_factory()
    user_name: str | None = str_small_factory(None)


class RequestList(BaseScheme):
    last_offset_id: int = num_factory()
    limit: int = num_factory()
    user_id: str = str_small_factory()
    role: str = str_small_factory()
    search_role: str | None = str_small_factory(None)
    search: str | None = str_small_factory(None)
    geo_id: int | None = num_factory(None)
    direction: str | None = str_small_factory(),
    status: str | None = str_small_factory(),
    amount_from: int | None = num_factory()
    amount_to: int | None = num_factory()
    create_timestamp_from: int | None = num_factory(),
    create_timestamp_to: int | None = num_factory()


class ResponseList(BaseScheme):
    items: List[Response]


class RequestUpdateStatus(BaseScheme):
    status: str | None = str_small_factory()
    id: str = str_small_factory()
    hash: str | None = str_small_factory()


class RequestUpdateStatusDB(RequestUpdateStatus):
    user_id: str = str_small_factory()


class ExportInternalTransactionsRequest(BaseScheme):
    user_id: str | None = str_small_factory()
    status: str | None = str_small_factory()
    direction: str | None = str_small_factory()
    amount_from: int | None = num_factory()
    amount_to: int | None = num_factory()
    role: str | None = str_small_factory()



class ExportInternalTransactionsResponse(BaseScheme):
    create_timestamp : datetime
    name : str
    amount : float
    address : str
    blockchain_transaction_hash : str | None

