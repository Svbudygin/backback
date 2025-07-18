from typing import Generic, List, TypeVar, Optional

from pydantic import BaseModel

T = TypeVar("T")


class GenericListResponseWithTypes(BaseModel, Generic[T]):
    types: Optional[List[str]] = []
    items: List[T]

class GenericListResponse(BaseModel, Generic[T]):
    items: List[T]

class GenericMerchStatisticRespone(BaseModel):
    conversion_rate: float = 0.0
    accepted_transactions: int = 0
    total_transactions: int = 0
    count_type: int = 0
    no_pending_transactions: int = 0
    total_teams: int = 0
    details_issuance: float = 0.0
    total_transactions_with_errors: int = 0
    pending_inbound: int = 0
    pending_outbound: int = 0
    trust_balance: int = 0
    locked_balance: int = 0
    credit_factor: int = 0
