from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

from app.core.constants import Limit


class BaseScheme(BaseModel):
    pass


def str_big_factory(default=PydanticUndefined, max_length=Limit.MAX_STRING_LENGTH_BIG):
    return Field(default, max_length=max_length)


def str_small_factory(default=PydanticUndefined):
    return Field(default, max_length=Limit.MAX_STRING_LENGTH_SMALL)


def num_factory(default=PydanticUndefined):
    return Field(default, ge=Limit.MIN_INT, le=Limit.MAX_INT)
