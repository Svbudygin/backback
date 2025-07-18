from app.core.constants import Limit
from app.models import UserModel
from app.models.BaseModel import BaseModel
import uuid
from typing import Optional, List, Tuple
from sqlalchemy import String, JSON, func, Boolean, TIMESTAMP, ForeignKey, BigInteger, Index, Identity, UniqueConstraint, TIME
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import time


class BankDetailModel(BaseModel):
    __tablename__ = "bank_detail_model"
    
    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        default=lambda _: str(uuid.uuid4()))
    
    team_id: Mapped[str] = mapped_column(ForeignKey('user_model.id'), nullable=False, index=True)
    
    name: Mapped[Optional[str]] = mapped_column(String(Limit.MAX_STRING_LENGTH_BIG), nullable=True)
    
    bank: Mapped[Optional[str]] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True)

    alias: Mapped[Optional[str]] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True)

    payment_system: Mapped[Optional[str]] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True, index=True)
    
    type: Mapped[Optional[str]] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True, index=True)
    
    number: Mapped[str] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=False)

    second_number: Mapped[Optional[str]] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True,
                                                         default=None, index=True)

    profile_id: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        index=True,
        nullable=True
    )


    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp())
    
    update_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    last_transaction_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    last_accept_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    last_disable: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False
    )

    today_amount_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    max_today_amount_used: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=(2 ** 32) - 1,
    )

    today_transactions_count: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")

    max_today_transactions_count: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")

    period_start_time: Mapped[time] = mapped_column(
        TIME,
        nullable=True
    )

    period_finish_time: Mapped[time] = mapped_column(
        TIME,
        nullable=True
    )

    transactions_count_limit: Mapped[Optional[List[Tuple[str, str, int, int]]]] = mapped_column(
        JSON,
        nullable=True,
    )

    pending_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    max_pending_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)

    auto_managed: Mapped[bool] = mapped_column(Boolean(), nullable=False, index=True, default=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, index=True)

    is_auto_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, index=True)
    
    is_deleted: Mapped[bool] = mapped_column(Boolean(), nullable=False, index=True)
    
    amount_limit: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    amount_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    device_hash: Mapped[Optional[str]] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=True)
    
    comment: Mapped[Optional[str]] = mapped_column(String(Limit.MAX_STRING_LENGTH_BIG), nullable=True)

    is_vip: Mapped[bool] = mapped_column(Boolean(), nullable=False, index=True, default=False)

    count_vip_payers: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    max_vip_payers: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    offset_id: Mapped[BigInteger] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
        nullable=False
    )

    fiat_max_inbound: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=(2 ** 32) - 1,
    )

    fiat_min_inbound: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0
    )

    delay: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")

    need_check_automation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="FALSE")
    
    __table_args__ = (
        Index('bank_detail_model_offset_id_index', 'offset_id'),
        Index('bank_detail_model_offset_id_index', 'number', 'bank', 'type', 'is_deleted'),
        Index("idx_bank_detail_vip", "is_vip"),
        Index("idx_bank_detail_active_deleted_vip", "is_active", "is_deleted", "is_vip"),
        Index("idx_bank_detail_team_active_deleted", "team_id", "is_deleted", "is_active"),
        Index("idx_bank_detail_fiat_range", "fiat_min_inbound", "fiat_max_inbound"),
        Index("idx_bank_detail_vip_payers_limit", "count_vip_payers", "max_vip_payers"),
        Index("idx_bdm_id_last_disable", "id", "last_disable")
    )
