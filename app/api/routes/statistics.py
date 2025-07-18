from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.responses import Response

from app.api import deps
from app.api.deps import v2_get_current_user
from app.functions.analytics import get_daily_traffic_stats, get_conversion_stats, get_teams_info
from app.functions.statistics import *
import app.schemas.StatisticsScheme as Ss
from app.schemas.UserScheme import UserSchemeResponse, User
from app.core.constants import (
    BalanceStatsPeriodName,
)
from app.utils.time import get_period_dates
from app.repositories.transactions_repository import get_create_timestamp_from, get_create_timestamp_to

router = APIRouter()


class UserIds(BaseModel):
    merchant_ids: list[str]
    agent_id: str


@router.get("/base")
async def list_transaction_route(
        period_name: BalanceStatsPeriodName,
        direction: str,
        create_timestamp_from: int | None = None,
        create_timestamp_to: int | None = None,
        current_user: UserSchemeResponse = Depends(v2_get_current_user),
) -> Ss.StatisticsResponse:
    date_from = get_create_timestamp_from(create_timestamp_from)
    date_to = get_create_timestamp_to(create_timestamp_to)
    if create_timestamp_from is None and create_timestamp_to is None:
        date_from, date_to = await get_period_dates(period_name=period_name)
    """Get statistics"""
    statistics_params = Ss.StatisticsRequest(
        user_id=current_user.id,
        balance_id=current_user.balance_id,
        role=current_user.role,
        date_from=date_from,
        date_to=date_to,
        direction=direction
    )
    
    result = await calculate_statistics(request=statistics_params)
    return result


@router.post('/daily-traffic-stats-1d')
async def get_statistics(ids: UserIds) -> Response:
    result = await get_daily_traffic_stats(merchant_ids=ids.merchant_ids,
                                           agent_id=ids.agent_id,
                                           day_period=7,
                                           hour_start=7
                                           )
    headers = {'Content-Disposition': 'attachment; filename="traffic.xlsx"'}
    return Response(result, media_type='application/ms-excel', headers=headers)


@router.post('/daily-traffic-stats-1h')
async def get_statistics(ids: UserIds) -> Response:
    result = await get_daily_traffic_stats(merchant_ids=ids.merchant_ids,
                                           agent_id=ids.agent_id,
                                           day_period=24,
                                           hour_start=0,
                                           is_daily=False
                                           )
    headers = {'Content-Disposition': 'attachment; filename="traffic.xlsx"'}
    return Response(result, media_type='application/ms-excel', headers=headers)


@router.post('/conversion-stats')
async def get_conversion(ids: UserIds) -> Response:
    result = await get_conversion_stats(merchant_ids=ids.merchant_ids)
    
    headers = {'Content-Disposition': 'attachment; filename="conversion.xlsx"'}
    return Response(result, media_type='application/ms-excel', headers=headers)


@router.post('/teams-info')
async def get_teams(ids: UserIds) -> Response:
    result = await get_teams_info(merchant_ids=ids.merchant_ids)
    headers = {'Content-Disposition': 'attachment; filename="teams.xlsx"'}
    return Response(result, media_type='application/ms-excel', headers=headers)

@router.post('/week_turnover')
async def get_week_turnover(id: str) -> Ss.WeekTurnoverResponse:
    result = await get_week_turnover_calc(id=id)
    return result
