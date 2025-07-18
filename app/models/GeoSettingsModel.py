from datetime import time
from sqlalchemy import Integer, ForeignKey, Boolean, Time
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import false, true

from app.models import BaseModel


class GeoSettingsModel(BaseModel):
    __tablename__ = 'geo_settings'

    id: Mapped[int] = mapped_column(Integer, ForeignKey('geo.id'), primary_key=True)

    max_outbound_pending_per_token: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='10'
    )

    block_deposit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false()
    )

    max_count_hold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='4'
    )

    max_transfer_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='4'
    )

    max_inbound_close_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='99'
    )

    get_back_transactions_time_s: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='7200'
    )

    is_auto_accept_appeals_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=false()
    )

    auto_accept_appeals_pause_time_from: Mapped[time] = mapped_column(
        Time,
        nullable=True
    )

    auto_accept_appeals_pause_time_to: Mapped[time] = mapped_column(
        Time,
        nullable=True
    )

    auto_accept_appeals_downtime_s: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )

    auto_close_outbound_transactions_s: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='1800'
    )

    req_after_enable_max_pay_in_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='1000'
    )

    req_after_enable_max_pay_in_automation_time: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='1800'
    )
