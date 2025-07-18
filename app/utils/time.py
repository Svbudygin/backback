from datetime import datetime, timedelta, time
from typing import Optional

from app.core.constants import BalanceStatsPeriodName, TrafficStatsPeriodName


async def get_period_dates(*, period_name):
    now = datetime.utcnow()

    if period_name == BalanceStatsPeriodName.hour:
        date_from = now.replace(minute=0, second=0, microsecond=0)
        date_to = now
    elif period_name == BalanceStatsPeriodName.last_hour:
        date_to = now.replace(minute=0, second=0, microsecond=0)
        date_from = date_to - timedelta(hours=1)
    elif period_name == BalanceStatsPeriodName.day:
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = now
    elif period_name == BalanceStatsPeriodName.last_day:
        date_to = now.replace(hour=0, minute=0, second=0, microsecond=0)
        date_from = date_to - timedelta(days=1)
    elif period_name == BalanceStatsPeriodName.all_time:
        date_from = datetime(2000, 1, 1)
        date_to = datetime(2100, 1, 1)
    else:
        raise ValueError(
            "Invalid period_name. Choose from 'hour', 'last_hour', 'day', 'last_day', 'all_time'."
        )

    return date_from, date_to


async def get_traffic_period_dates(*, period_name):
    now = datetime.utcnow()

    if period_name == TrafficStatsPeriodName.hour:
        date_from = now - timedelta(hours=1)
    elif period_name == TrafficStatsPeriodName.day:
        date_from = now - timedelta(days=1)
    elif period_name == TrafficStatsPeriodName.minutes:
        date_from = now - timedelta(minutes=15)
    else:
        raise ValueError(
            "Invalid period_name. Choose from 'hour', 'day', 'minutes'."
        )

    return date_from


def time_without_pause(x: datetime, current_time: datetime, pause_from: time, pause_to: time) -> int:
    if x > current_time:
        x, current_time = current_time, x

    total = timedelta()
    day = x.date()

    while day <= current_time.date():
        start_of_day = datetime.combine(day, time(0, 0))
        end_of_day = datetime.combine(day, time(23, 59, 59, 999999))

        interval_start = max(x, start_of_day)
        interval_end = min(current_time, end_of_day)

        if interval_start > interval_end:
            day += timedelta(days=1)
            continue

        pause_start = datetime.combine(day, pause_from)
        pause_end = datetime.combine(day, pause_to)

        if pause_start < interval_end and pause_end > interval_start:
            pause_overlap_start = max(pause_start, interval_start)
            pause_overlap_end = min(pause_end, interval_end)
            pause_duration = pause_overlap_end - pause_overlap_start
        else:
            pause_duration = timedelta(0)

        total += (interval_end - interval_start - pause_duration)
        day += timedelta(days=1)

    return int(total.total_seconds())


def calculate_end_time_with_pause(
        start: datetime,
        duration: int,
        pause_start: Optional[time] = None,
        pause_end: Optional[time] = None
) -> datetime:
    if pause_start is None or pause_end is None:
        return start + timedelta(seconds=duration)

    if pause_start == pause_end:
        return start + timedelta(seconds=duration)
    
    start_time = start.time()
    start_date = start.date()
    
    is_during_pause = False
    if pause_end > pause_start:
        is_during_pause = pause_start <= start_time < pause_end
    else:
        is_during_pause = start_time >= pause_start or start_time < pause_end
    
    if is_during_pause:
        if start_time >= pause_start:
            start_date += timedelta(days=1)
        start = datetime.combine(start_date, pause_end)

        return start + timedelta(seconds=duration)

    pause_duration_seconds = (
            (pause_end.hour * 3600 + pause_end.minute * 60 + pause_end.second) -
            (pause_start.hour * 3600 + pause_start.minute * 60 + pause_start.second)
    )
    if pause_duration_seconds <= 0:
        pause_duration_seconds += 24 * 3600

    workday_seconds = 24 * 3600 - pause_duration_seconds

    end_without_pauses = start + timedelta(seconds=duration)
    first_day_pause_start = datetime.combine(start.date(), pause_start)

    if end_without_pauses <= first_day_pause_start:
        return end_without_pauses

    remaining_seconds = duration - (first_day_pause_start - start).total_seconds()
    if remaining_seconds <= 0:
        return first_day_pause_start + timedelta(seconds=remaining_seconds)

    full_days = remaining_seconds // workday_seconds
    remaining_seconds %= workday_seconds

    current_time = datetime.combine(start.date(), pause_end) + timedelta(days=1 if pause_end <= pause_start else 0)
    current_time += timedelta(days=full_days)
    current_time += timedelta(seconds=remaining_seconds)

    return current_time
