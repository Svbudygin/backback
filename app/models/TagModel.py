import uuid
from sqlalchemy import String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import Limit
from app.models.BaseModel import BaseModel


class TagModel(BaseModel):
    __tablename__ = "tag_model"

    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        default=lambda _: str(uuid.uuid4()))

    code: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        unique=True,
        nullable=False
    )

    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )
