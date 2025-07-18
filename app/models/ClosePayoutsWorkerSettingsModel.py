from typing import Optional
from sqlalchemy import ForeignKey, Integer, BigInteger, String, ARRAY, Boolean, false
from sqlalchemy.orm import Mapped, mapped_column

from app.models.BaseModel import BaseModel


class ClosePayoutsWorkerSettingsModel(BaseModel):
    __tablename__ = 'close_payouts_worker_settings'
    
    geo_id: Mapped[int] = mapped_column(Integer, ForeignKey('geo.id'), primary_key=True)

    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())

    amount_ge: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    amount_le: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    type_in: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    type_not_in: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    bank_in: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    bank_not_in: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    last_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
