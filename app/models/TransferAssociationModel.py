from sqlalchemy import String, Index, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.BaseModel import BaseModel
from datetime import datetime

class TransferAssociationModel(BaseModel):
    __tablename__ = "transfer_association_model"

    team_id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)

    transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)

    transfer_from_team_timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    __table_args__ = (
        Index("idx_transfer_association_team_id", "team_id"),
        Index("idx_transfer_association_transaction_id", "transaction_id"),
        Index("idx_transfer_association_timestamp_id", "transfer_from_team_timestamp"),
    )
