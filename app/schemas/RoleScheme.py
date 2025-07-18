from pydantic import ConfigDict, field_validator
from typing import List, Optional

from app.schemas.BaseScheme import BaseScheme


class PermissionScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str


class RoleScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    permissions: List[PermissionScheme]


class CreateRoleScheme(BaseScheme):
    name: str
    permissions: List[int]


class UpdateRoleScheme(BaseScheme):
    name: Optional[str]
    permissions: Optional[List[int]]
