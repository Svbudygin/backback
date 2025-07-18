from sqlalchemy import ForeignKey, BigInteger, String, Boolean, Integer, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import UserModel
from app.core.constants import Limit


class TeamModel(UserModel):
    __tablename__ = 'teams'

    id: Mapped[str] = mapped_column(
        ForeignKey('user_model.id'),
        primary_key=True
    )

    geo_id: Mapped[int] = mapped_column(
        ForeignKey("geo.id"),
    )

    geo: Mapped["GeoModel"] = relationship(lazy="joined")

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

    fiat_max_outbound: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=(2 ** 32) - 1,
    )

    fiat_min_outbound: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0
    )

    today_outbound_amount_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    max_today_outbound_amount_used: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=(2 ** 32) - 1,
    )

    last_transaction_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

    priority_inbound: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='100'
    )

    max_outbound_pending_per_token: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )

    max_inbound_pending_per_token: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )

    count_pending_inbound: Mapped[int] = mapped_column(
        Integer,
        nullable = False,
        server_default = '0'
    )

    __mapper_args__ = {
        'polymorphic_load': 'selectin',
        'polymorphic_identity': 'team',
    }
