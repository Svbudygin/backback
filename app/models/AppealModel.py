from typing import Optional
from datetime import datetime
import uuid
from sqlalchemy import (
    String,
    TIMESTAMP,
    func,
    ForeignKey,
    BigInteger,
    ARRAY,
    Boolean,
    Identity,
    event,
    false
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Limit
from app.models.BaseModel import BaseModel


class AppealModel(BaseModel):
    __tablename__ = "appeals"

    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        index=True,
        default=lambda _: str(uuid.uuid4()),
    )

    create_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    update_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False
    )

    close_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        ForeignKey("external_transaction_model.id")
    )
    transaction: Mapped["ExternalTransactionModel"] = relationship(lazy="joined")

    merchant_appeal_id: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        unique=True
    )

    finalization_callback_uri: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True
    )

    ask_statement_callback_uri: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True
    )

    amount: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True
    )

    receipts: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String),
        nullable=True
    )

    merchant_statements: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String),
        nullable=True
    )

    team_statements: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String),
        nullable=True
    )

    is_merchant_statement_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    is_team_statement_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    is_support_confirmation_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    reject_reason: Mapped[str] = mapped_column(
        String,
        nullable=True
    )

    reject_comment: Mapped[str] = mapped_column(
        String,
        nullable=True
    )

    offset_id: Mapped[BigInteger] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        nullable=False
    )

    team_processing_start_time: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=True
    )

    timeout_expired: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false()
    )
