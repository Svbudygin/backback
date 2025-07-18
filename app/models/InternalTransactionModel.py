import uuid

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    ForeignKey,
    Identity,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import Limit
from app.models.BaseModel import BaseModel


class InternalTransactionModel(BaseModel):
    __tablename__ = "internal_transaction_model"

    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        default=lambda _: str(uuid.uuid4()),
    )

    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp(), index=True
    )

    amount: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    status: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=False, index=True
    )

    direction: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=False
    )

    address: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True
    )

    blockchain_transaction_hash: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True, unique=True
    )

    from_address: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("user_model.id"), nullable=False, index=True
    )

    # user: Mapped["UserModel"] = relationship("UserModel", backref="user_mode_from_internal_transaction",
    #                                          lazy='joined', innerjoin=True)

    offset_id: Mapped[BigInteger] = mapped_column(
        BigInteger, Identity(), primary_key=True, nullable=False, index=True
    )
