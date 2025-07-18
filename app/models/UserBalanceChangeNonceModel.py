import uuid

from sqlalchemy import String, ForeignKey, BigInteger, Identity, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Limit
from app.models import ExternalTransactionModel
from app.models.BaseModel import BaseModel


class UserBalanceChangeNonceModel(BaseModel):
    __tablename__ = 'user_balance_change_nonce_model'
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        unique=True,
        index=True,
        nullable=False
    )
    
    change_id: Mapped[int] = mapped_column(BigInteger,
                                           nullable=False,
                                           index=True,
                                           default=0)

    balance_id: Mapped[str | None] = mapped_column(
        nullable=True, unique=True,
        index=True)
    
    profit_balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    trust_balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    locked_balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    fiat_profit_balance: Mapped[int] = mapped_column(BigInteger, nullable=True, default=0)  # TODO make non null
    
    fiat_trust_balance: Mapped[int] = mapped_column(BigInteger, nullable=True, default=0)  # TODO make non null
    
    fiat_locked_balance: Mapped[int] = mapped_column(BigInteger, nullable=True, default=0)  # TODO make non null
