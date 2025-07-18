from app.schemas.BaseScheme import BaseScheme, num_factory, str_small_factory
from datetime import datetime


class StatisticsRequest(BaseScheme):
    user_id: str = str_small_factory()
    balance_id: str = str_small_factory()
    role: str = str_small_factory()
    date_from: datetime = None
    date_to: datetime = None
    direction: str = str_small_factory()


class StatisticsResponse(BaseScheme):
    total_volume: int = num_factory()
    profit: int = num_factory()
    accept: int = num_factory()
    decline: int = num_factory()
    #pending: int = num_factory()


class WeekTurnoverResponse(BaseScheme):
    date_from: datetime = None
    date_to: datetime = None
    pay_in: int = num_factory()
    pay_out: int = num_factory()
