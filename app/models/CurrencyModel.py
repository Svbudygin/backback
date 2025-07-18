import uuid
from typing import Optional
from sqlalchemy import String, func, Boolean, BigInteger, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import Limit
from app.models.BaseModel import BaseModel


class CurrencyModel(BaseModel):
    __tablename__ = "currency_model"
    
    id: Mapped[str] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL),
                                    nullable=False,
                                    primary_key=True,
                                    unique=True)
    
    name: Mapped[str] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True)
    
    exchange_rate: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    
    inbound_exchange_rate: Mapped[int] = mapped_column(BigInteger(), nullable=True)
    outbound_exchange_rate: Mapped[int] = mapped_column(BigInteger(), nullable=True)
    
    update_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp())
