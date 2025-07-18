import uuid

from sqlalchemy import String, ForeignKey, BigInteger, Identity, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Limit
from app.models import ExternalTransactionModel
from app.models.BaseModel import BaseModel


class StatisticsModel(BaseModel):
    __tablename__ = 'statistics_model'
    
    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        default=lambda _: str(uuid.uuid4()))
    
    external_transaction_id: Mapped[str] = mapped_column(ForeignKey('external_transaction_model.id'),
                                                         nullable=False,
                                                         index=True)
    
    user_id: Mapped[str] = mapped_column(ForeignKey('user_model.id'),
                                         nullable=False,
                                         index=True)
    
    profit_balance_change: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    trust_balance_change: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    direction: Mapped[str] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=False)
    
    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        index=True
    )
    
    offset_id: Mapped[BigInteger] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        nullable=False,
        index=True
    )
