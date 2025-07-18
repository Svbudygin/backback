from sqlalchemy import ForeignKey, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.inspection import inspect

from app.models.BaseModel import BaseModel


class AccessMatrix(BaseModel):
    __tablename__ = 'access_matrix'

    user_id: Mapped[str] = mapped_column(
        ForeignKey('user_model.id'),
        primary_key=True
    )
    user: Mapped["UserModel"] = relationship(back_populates="access_matrix")

    view_traffic: Mapped[bool] = mapped_column(Boolean, default=False)
    view_fee: Mapped[bool] = mapped_column(Boolean, default=False)
    view_pay_in: Mapped[bool] = mapped_column(Boolean, default=False)
    view_pay_out: Mapped[bool] = mapped_column(Boolean, default=False)
    view_supports: Mapped[bool] = mapped_column(Boolean, default=False)
    view_wallet: Mapped[bool] = mapped_column(Boolean, default=False)
    view_agents: Mapped[bool] = mapped_column(Boolean, default=False)
    view_merchants: Mapped[bool] = mapped_column(Boolean, default=False)
    view_teams: Mapped[bool] = mapped_column(Boolean, default=False)
    view_search: Mapped[bool] = mapped_column(Boolean, default=False)
    view_compensations: Mapped[bool] = mapped_column(Boolean, default=False)
    view_sms_hub: Mapped[bool] = mapped_column(Boolean, default=False)
    view_accounting: Mapped[bool] = mapped_column(Boolean, default=False)
    view_details: Mapped[bool] = mapped_column(Boolean, default=False)
    view_appeals: Mapped[bool] = mapped_column(Boolean, default=False)
    view_analytics: Mapped[bool] = mapped_column(Boolean, default=False)

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs if c.key != 'user_id'}
