import uuid
from typing import Optional
from sqlalchemy import String, func, Boolean, BigInteger, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import Limit
from app.models.BaseModel import BaseModel


class WalletModel(BaseModel):
    __tablename__ = "wallet_model"
    
    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        default=lambda _: str(uuid.uuid4())
    )
    
    wallet_address: Mapped[str] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), unique=True, nullable=False)
