from typing import TypeVar, Generic, List
from pydantic import Field
from pydantic.generics import GenericModel

from app.schemas.BaseScheme import BaseScheme
from app.core.constants import Limit


ResponseSchemaType = TypeVar('ResponseSchemaType', bound=BaseScheme)


class PaginationParams(BaseScheme):
    offset: int = Field(Limit.MAX_INT, ge=0, le=Limit.MAX_INT, alias="last_offset_id")
    limit: int = Field(10, ge=10, le=200)


class PaginationResponse(GenericModel, Generic[ResponseSchemaType]):
    page: int
    size: int
    items: List[ResponseSchemaType]
