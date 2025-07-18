from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import BaseModel


class GeoModel(BaseModel):
    __tablename__ = 'geo'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        unique=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(String, unique=True, index=True)
