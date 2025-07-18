from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.models import UserModel


class SupportModel(UserModel):
    __tablename__ = 'supports'

    id: Mapped[str] = mapped_column(
        ForeignKey('user_model.id'),
        primary_key=True
    )

    __mapper_args__ = {
        'polymorphic_load': 'selectin',
        'polymorphic_identity': 'support',
    }
