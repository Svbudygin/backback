import uuid

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Integer,
    Boolean,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
    sql,
    desc,
    Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.event import listens_for
from typing import Optional

from app.core.constants import Limit
from app.enums import TransactionFinalStatusEnum
from app.models.BaseModel import BaseModel


class ExternalTransactionModel(BaseModel):
    __tablename__ = "external_transaction_model"

    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        index=True,
        default=lambda _: str(uuid.uuid4()),
    )

    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp(), index=True
    )

    priority: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True
    )

    amount: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    exchange_rate: Mapped[int] = mapped_column(BigInteger, nullable=False)

    reason: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=False, index=True
    )

    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False)

    direction: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=False, index=True
    )

    bank_detail_id: Mapped[str | None] = mapped_column(
        ForeignKey("bank_detail_model.id"), nullable=True, index=True
    )

    bank_detail: Mapped["BankDetailModel"] = relationship(lazy='noload', foreign_keys=[bank_detail_id])

    bank_detail_number: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG), nullable=True, index=True
    )

    bank_detail_bank: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True, index=True
    )

    bank_detail_name: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        nullable=True,
    )

    type: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True, index=True
    )

    economic_model: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True
    )  # TODO non null

    team_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_model.id"), nullable=True, index=True
    )

    team: Mapped["TeamModel"] = relationship(lazy='noload', foreign_keys=[team_id])

    merchant_id: Mapped[str] = mapped_column(
        ForeignKey("user_model.id"), nullable=False, index=True
    )

    merchant: Mapped["MerchantModel"] = relationship(lazy='noload', foreign_keys=[merchant_id])

    merchant_payer_id: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True
    )

    merchant_transaction_id: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True, unique=True
    )

    hook_uri: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG), nullable=True
    )

    file_uri: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG), nullable=True
    )

    additional_info: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG), nullable=True
    )

    currency_id: Mapped[str] = mapped_column(nullable=False, index=True)

    offset_id: Mapped[BigInteger] = mapped_column(
        BigInteger, Identity(), primary_key=True, nullable=False, index=True
    )

    tag_id: Mapped[str] = mapped_column(
        ForeignKey("tag_model.id"), nullable=False
    )

    transfer_to_team_timestamp = mapped_column(
        TIMESTAMP, nullable=True
    )

    final_status_timestamp = mapped_column(
        TIMESTAMP, nullable=True
    )

    count_hold: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default='0'
    )

    transfer_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default='0'
    )

    final_status: Mapped[Optional[TransactionFinalStatusEnum]] = mapped_column(
        Enum(TransactionFinalStatusEnum, values_callable=lambda x: [e.value for e in x], name='transaction_final_status_enum'),
        nullable=True
    )

    __table_args__ = (
        Index(
            "external_transaction_device_index",
            "status",
            "team_id",
            "direction",
            "amount",
        ),
        Index(
            "idx_etm_bdid_fst_desc",
            "bank_detail_id",
            desc("final_status_timestamp"),
        )
    )


@listens_for(ExternalTransactionModel, 'before_insert')
def set_default_tag_id(mapper, connection, target):
    if target.tag_id is None:
        target.tag_id = sql.expression.text("DEFAULT")
