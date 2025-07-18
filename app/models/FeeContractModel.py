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
    sql
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.event import listens_for

from app.core.constants import Limit
from app.models import UserModel
from app.models.BaseModel import BaseModel


class FeeContractModel(BaseModel):
    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        index=True,
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

    comment: Mapped[Optional[str]] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_BIG), nullable=True
    )

    offset_id: Mapped[BigInteger] = mapped_column(
        BigInteger, Identity(), primary_key=True, nullable=False, index=True
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("user_model.id"), nullable=False, index=True
    )

    tag_id: Mapped[str] = mapped_column(
        ForeignKey("tag_model.id"), nullable=False
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        backref="user_mode_from_fee_contract",
        lazy="noload",
        innerjoin=True,
        foreign_keys=[user_id],
    )

    team: Mapped["UserModel"] = relationship(
        "UserModel",
        backref="team_mode_from_fee_contract",
        lazy="noload",
        innerjoin=True,
        foreign_keys=[team_id],
    )

    merchant: Mapped["UserModel"] = relationship(
        "UserModel",
        backref="merchant_mode_from_fee_contract",
        lazy="noload",
        innerjoin=True,
        foreign_keys=[merchant_id],
    )

    inbound_fee: Mapped[int] = mapped_column(BigInteger, nullable=False)

    outbound_fee: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        Index("fee_contract_model_index", "merchant_id", "team_id", "is_deleted"),
    )

    __tablename__ = "fee_contract_model"


@listens_for(FeeContractModel, 'before_insert')
def set_default_tag_id(mapper, connection, target):
    if target.tag_id is None:
        target.tag_id = sql.expression.text("DEFAULT")
