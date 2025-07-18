from typing import Optional
from sqlalchemy import ForeignKey, BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import text

from app.models import UserModel
from app.core.constants import Limit


class MerchantModel(UserModel):
    __tablename__ = 'merchants'

    id: Mapped[str] = mapped_column(
        ForeignKey('user_model.id'),
        primary_key=True
    )

    geo_id: Mapped[int] = mapped_column(
        ForeignKey("geo.id"),
    )

    geo: Mapped["GeoModel"] = relationship(lazy="joined")

    transaction_auto_close_time_s: Mapped[int] = mapped_column(
        BigInteger,
        server_default=text('15 * 60')
    )

    transaction_outbound_auto_close_time_s: Mapped[int] = mapped_column(
        BigInteger,
        server_default=text('24 * 60 * 60')
    )

    credit_factor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default='0'
    )

    api_secret: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        nullable=False,
        unique=True
    )

    economic_model: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        nullable=False,
        server_default='crypto_fiat_profit'
    )

    is_inbound_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default='FALSE'
    )

    is_outbound_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default='FALSE'
    )

    # telegram_verifier_chat_id: Mapped[Optional[str]] = mapped_column(
    #     String(Limit.MAX_STRING_LENGTH_SMALL),
    #     nullable=True
    # )

    currency_id: Mapped[str] = mapped_column(
        ForeignKey("currency_model.id")
    )

    currency: Mapped["CurrencyModel"] = relationship(lazy="joined")

    left_eps_change_amount_allowed: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default='0'
    )

    right_eps_change_amount_allowed: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default='0'
    )

    min_fiat_amount_in: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default='0'
    )

    max_fiat_amount_in: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default='4294967295'
    )

    is_whitelist: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default='FALSE'
    )

    __mapper_args__ = {
        'polymorphic_load': 'selectin',
        'polymorphic_identity': 'merchant',
    }
