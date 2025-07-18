from sqlalchemy import Integer, ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from typing import Optional

from app.models import BaseModel, WalletModel
from app.core.constants import Limit


class NamespaceModel(BaseModel):
    __tablename__ = 'namespaces'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        unique=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True
    )

    wallet_id: Mapped[str] = mapped_column(
        ForeignKey('wallet_model.id', ondelete='CASCADE'),
    )
    wallet: Mapped["WalletModel"] = relationship(foreign_keys=[wallet_id])

    withdraw_wallet_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey('wallet_model.id', ondelete='CASCADE'),
    )
    withdraw_wallet: Mapped[Optional["WalletModel"]] = relationship(foreign_keys=[withdraw_wallet_id])

    telegram_bot_secret: Mapped[Optional[str]] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        nullable=True
    )
