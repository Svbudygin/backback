from typing import List
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import BaseModel, PermissionModel, role_permission_association_table
from app.core.constants import Limit


class RoleModel(BaseModel):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        unique=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG),
        unique=True
    )

    permissions: Mapped[List["PermissionModel"]] = relationship(
        secondary=role_permission_association_table,
        lazy='selectin'
    )
