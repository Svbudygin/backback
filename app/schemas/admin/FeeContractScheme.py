from datetime import datetime
from typing import List

from fastapi import HTTPException
from pydantic import field_validator
from pydantic_core.core_schema import FieldValidationInfo, ValidationInfo

from app.core.constants import Role
from app.schemas.BaseScheme import BaseScheme, str_small_factory, num_factory


class FeeContractResponse(BaseScheme):
    id: str | None = None
    user_id: str | None = None
    inbound_fee: int
    outbound_fee: int
    role: str
    create_timestamp: datetime | None = None
    name: str | None
    tag_id: str | None
    tag_name: str | None

class FeeContractBatchRequest(BaseScheme):
    user_id: str = str_small_factory()
    inbound_fee: int = num_factory()
    outbound_fee: int = num_factory()
    
    @field_validator('inbound_fee', 'outbound_fee')
    @classmethod
    def validate_fees(cls, fee: int):
        if fee < 0:
            raise HTTPException(status_code=422, detail='fees must be positive')
        return fee
    

class FeeContractsBatchCreateRequest(BaseScheme):
    merchant_id: str
    team_id: str
    tag_id: str
    fee_contracts: List[FeeContractBatchRequest]


class FeeContractCopy(BaseScheme):
    merchant_id_from: str
    merchant_id_to: str
    tag_id: str | None = None


class FeeContractBulkChange(BaseScheme):
    delta: int
    increase_id: str | None = None
    decrease_id: str | None = None
    merchant_id: str | None = None
    tag_id: str | None = None
    direction: str
