from sqlalchemy import String, Index, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.BaseModel import BaseModel

class WhiteListPayerModel(BaseModel):
    __tablename__ = "whitelist_payer_id_model"

    payer_id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)

    __table_args__ = (
        Index("idx_whitelist_payer_merchant", "payer_id"),
    )
