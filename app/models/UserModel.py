import uuid
from typing import Optional
from sqlalchemy import String, func, Boolean, TIMESTAMP, ForeignKey, case, BigInteger, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Limit
from app.models.BaseModel import BaseModel


class UserModel(BaseModel):
    __tablename__ = "user_model"
    
    id: Mapped[str] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        primary_key=True,
        unique=True,
        default=lambda _: str(uuid.uuid4())
    )

    offset_id: Mapped[BigInteger] = mapped_column(
        BigInteger,
        Identity(),
        unique=True,
        nullable=False
    )
    
    balance_id: Mapped[str | None] = mapped_column(
        String(Limit.MAX_STRING_LENGTH_SMALL),
        index=True,
        nullable=True
    )
    
    password_hash: Mapped[str] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), unique=True, nullable=False)
    
    name: Mapped[str] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=False)
    
    role: Mapped[str] = mapped_column(String(Limit.MAX_STRING_LENGTH_SMALL), nullable=False, index=True)
    
    create_timestamp: Mapped[int] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )
    
    is_blocked: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    namespace_id: Mapped[int] = mapped_column(ForeignKey('namespaces.id'), nullable=True)
    namespace: Mapped["NamespaceModel"] = relationship(lazy='joined')

    user_role_id: Mapped[Optional[int | None]] = mapped_column(ForeignKey('roles.id'), nullable=True)
    user_role: Mapped["RoleModel"] = relationship(lazy='joined')

    access_matrix: Mapped["AccessMatrix"] = relationship(back_populates="user", lazy='joined')

    is_autowithdraw_enabled: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=True,
        default=False
    )

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': case(
            (role == 'agent', 'user'),
            (role == 'tv_worker', 'user'),
            (role == 'c_worker', 'user'),
            (role == 'b_worker', 'user'),
            (role == 'tc_worker', 'user'),
            (role == 'merchant', 'merchant'),
            (role == 'team', 'team'),
            (role == 'support', 'support'),
            else_='user'
        ),
        'with_polymorphic': '*'
    }
