from sqlalchemy import String, Index, ForeignKey, TIMESTAMP, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.BaseModel import BaseModel
from app.core.constants import Limit
from datetime import datetime
import uuid

class VipPayerModel(BaseModel):
    __tablename__ = "vip_payer_model"

    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        index=True,
        default=lambda _: str(uuid.uuid4()),
    )

    payer_id: Mapped[str] = mapped_column(String(64), nullable=False)

    bank_detail_id: Mapped[str] = mapped_column(
        String(64), nullable=False
    )

    last_transaction_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    last_accept_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=True
    )

    __table_args__ = (
        Index("idx_vip_payer", "payer_id"),
        Index("idx_vip_payer_bank", "bank_detail_id"),
        Index("idx_vip_payer_last_tx", "last_transaction_timestamp"),
        Index("idx_vip_payer_accept_tx", "last_accept_timestamp"),
        UniqueConstraint("payer_id", "bank_detail_id", name="uq_vip_payer_pair")
    )

# Функция, которая проверяет кол-во привязок у payer_id
#CREATE OR REPLACE FUNCTION check_vip_payer_limit()
#RETURNS trigger AS $$
#DECLARE
#    cnt INTEGER;
#    max_allowed INTEGER := 2;
#BEGIN
#    SELECT COUNT(*) INTO cnt
#    FROM vip_payer_model
#    WHERE payer_id = NEW.payer_id
#    AND LENGTH(bank_detail_id) = LENGTH(NEW.bank_detail_id);
#
#    IF cnt >= max_allowed THEN
#        RAISE EXCEPTION 'VIP payer has reached max allowed bank_detail links (%).', max_allowed;
#    END IF;
#
#    RETURN NEW;
#END;
#$$ LANGUAGE plpgsql;
#
# Создание триггера
#CREATE TRIGGER trg_check_vip_payer_limit
#BEFORE INSERT ON vip_payer_model
#FOR EACH ROW
#EXECUTE FUNCTION check_vip_payer_limit();
#
# Удаление триггера и функции(если пригодится)
#DROP TRIGGER IF EXISTS trg_check_vip_payer_limit ON vip_payer_model;
#DROP FUNCTION IF EXISTS check_vip_payer_limit;



