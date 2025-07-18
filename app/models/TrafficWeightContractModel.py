import uuid
from typing import Optional

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import Limit
from app.models.BaseModel import BaseModel


class TrafficWeightContractModel(BaseModel):
    __tablename__ = "traffic_weight_contact_model"

    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        default=lambda _: str(uuid.uuid4()),
    )

    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )

    is_deleted: Mapped[bool] = mapped_column(nullable=False)

    merchant_id: Mapped[str] = mapped_column(
        ForeignKey("user_model.id"), nullable=False
    )

    team_id: Mapped[str] = mapped_column(ForeignKey("user_model.id"), nullable=False)

    currency_id: Mapped[str] = mapped_column(
        ForeignKey("currency_model.id"), nullable=False
    )

    type: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=False, index=True
    )

    comment: Mapped[Optional[str]] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG), nullable=False
    )

    offset_id: Mapped[BigInteger] = mapped_column(
        BigInteger, Identity(), primary_key=True, nullable=False, index=True
    )

    inbound_traffic_weight: Mapped[int] = mapped_column(BigInteger, nullable=False)

    outbound_traffic_weight: Mapped[int] = mapped_column(BigInteger, nullable=False)

    outbound_amount_less_or_eq: Mapped[int] = mapped_column(BigInteger, nullable=True)

    outbound_amount_great_or_eq: Mapped[int] = mapped_column(BigInteger, nullable=True)

    outbound_bank_in: Mapped[str] = mapped_column(String(512), nullable=True)

    outbound_bank_not_in: Mapped[str] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        Index(
            "traffic_weight_contract_model_index",
            "merchant_id",
            "team_id",
            "currency_id",
        ),
    )
