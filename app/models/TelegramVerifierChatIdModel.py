from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import BaseModel
from app.core.constants import Limit


class TelegramVerifierChatIdModel(BaseModel):
    __tablename__ = 'telegram_verifier_chat_id'

    geo_id: Mapped[int] = mapped_column(
        ForeignKey('geo.id'),
        primary_key=True
    )

    namespace_id: Mapped[int] = mapped_column(
        ForeignKey('namespaces.id'),
        primary_key=True
    )

    chat_id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL)
    )
