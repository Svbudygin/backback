import uuid

from typing import Optional, Dict, List
from sqlalchemy import String, JSON, TIMESTAMP, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import Limit
from app.models.BaseModel import BaseModel

# TODO method to be field related to another table


class PaymentFormModel(BaseModel):
    __tablename__ = 'payment_forms'

    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        default=lambda _: str(uuid.uuid4())
    )

    merchant_transaction_id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL)
    )

    merchant_id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL)
    )

    hook_uri: Mapped[Optional[str]] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG),
        nullable=True
    )

    payer_id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL)
    )

    amount: Mapped[int] = mapped_column(
        BigInteger
    )

    return_url: Mapped[Optional[str]] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG),
        nullable=True
    )

    success_url: Mapped[Optional[str]] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG),
        nullable=True
    )

    fail_url: Mapped[Optional[str]] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG),
        nullable=True
    )

    merchant_website_name: Mapped[Optional[str]] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG),
        nullable=True
    )

    config: Mapped[List[Dict]] = mapped_column(JSON)

    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    links: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=None
    )

    method: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        default=None
    )

    currency_name: Mapped[str] = mapped_column(
        String
    )

    auto_close_time: Mapped[int] = mapped_column(
        BigInteger
    )
