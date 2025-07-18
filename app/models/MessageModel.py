import uuid

from sqlalchemy import String, ForeignKey, BigInteger, TIMESTAMP, func, UniqueConstraint, Identity
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import Limit
from app.models.BaseModel import BaseModel


class MessageModel(BaseModel):
    __tablename__ = 'message_model'
    
    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        default=lambda _: str(uuid.uuid4()))

    offset_id: Mapped[BigInteger] = mapped_column(
        BigInteger, Identity(), primary_key=True, nullable=False, index=True
    )
    
    external_transaction_id: Mapped[str | None] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL),
                                                                nullable=True,
                                                                index=True,
                                                                unique=True)
    
    user_id: Mapped[str] = mapped_column(ForeignKey('user_model.id'),
                                         nullable=True,
                                         index=True)
    
    title: Mapped[str | None] = mapped_column(String(Limit.MAX_STRING_LENGTH_BIG), nullable=True, index=True)
    
    text: Mapped[str | None] = mapped_column(String(Limit.MAX_STRING_LENGTH_BIG), nullable=True, index=True)
    
    amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    
    comment: Mapped[str | None] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True, index=True)
    
    device_hash: Mapped[str | None] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True, index=True)

    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        index=True
    )

    number: Mapped[str | None] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True, index=True)

    bank_detail_number: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG), nullable=True, index=True
    )