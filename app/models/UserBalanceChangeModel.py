import uuid

from sqlalchemy import String, ForeignKey, BigInteger, Identity, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Limit
from app.models import ExternalTransactionModel
from app.models.BaseModel import BaseModel


class UserBalanceChangeModel(BaseModel):
    __tablename__ = 'user_balance_change_model'
    
    id_pk: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        unique=True,
        nullable=False
    )
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        server_default=func.txid_current(),
        index=True,
        nullable=False
    )
    
    user_id: Mapped[str] = mapped_column(nullable=False,
                                         index=True)
    
    balance_id: Mapped[str | None] = mapped_column(
                                                   nullable=True,
                                                   index=True)
    
    transaction_id: Mapped[str] = mapped_column(nullable=True,
                                                index=True)
    
    profit_balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    trust_balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    locked_balance: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    fiat_profit_balance: Mapped[int] = mapped_column(BigInteger, nullable=True, default=0)  # TODO make non null
    
    fiat_trust_balance: Mapped[int] = mapped_column(BigInteger, nullable=True, default=0)  # TODO make non null
    
    fiat_locked_balance: Mapped[int] = mapped_column(BigInteger, nullable=True, default=0)  # TODO make non null
    
    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
    )
