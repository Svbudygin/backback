from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import BaseModel
from app.core.constants import Limit


class PermissionModel(BaseModel):
    __tablename__ = 'permissions'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        unique=True,
        autoincrement=True
    )

    code: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG),
        unique=True
    )
