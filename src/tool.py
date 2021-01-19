import logging
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import List, Iterable, Tuple, Set

from src import holidays
from src.calendar import Calendar
from src.clazz import Clazz


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def symbol_split(symbol: str) -> Tuple[str, str]:
    parts = symbol.split('.')
    return '.'.join(parts[:-1]), parts[-1]


def module_name(name: str) -> str:
    return name.split('.')[-1]


INTERVAL_1H = timedelta(hours=1)
INTERVAL_1D = timedelta(days=1)
INTERVAL_1W = timedelta(days=7)


def interval_name(interval: timedelta) -> str:
    return {
        INTERVAL_1H: '1h',
        INTERVAL_1D: '1d',
        INTERVAL_1W: '1w'
    }[interval]


@lru_cache(maxsize=16)
def exchange_holidays(exchange: str) -> Set[str]:
    return {Calendar.parse_datetime(d) for d in holidays.EXCHANGE_HOLIDAYS[exchange]}


def last_workday(exchange: str, dt: datetime) -> datetime:
    _holidays = exchange_holidays(exchange)
    d = dt.toordinal()
    while True:
        d -= 1
        day = datetime.fromordinal(d)
        day = day.replace(tzinfo=timezone.utc)
        if day.weekday() in (0, 1, 2, 3, 4) and day not in _holidays:
            return day


def last_sunday(dt: datetime) -> datetime:
    d = dt.toordinal()
    return datetime.fromordinal(d - (d % 7)).replace(tzinfo=timezone.utc)


def last_session(exchange: str, interval: timedelta, dt: datetime) -> datetime:
    """
    It returns datetime where all fields smaller than interval are set to zero.
    It is up to a data driver to modify it to meet a provider requirements.
    """
    if interval == INTERVAL_1H:
        return dt.replace(minute=0, second=0, microsecond=0)
    if interval == INTERVAL_1D:
        return last_workday(exchange, dt)
    if interval == INTERVAL_1W:
        return last_sunday(dt)


def is_latest(path: Path, interval: timedelta, exchange: str) -> bool:
    if path.exists():
        path_dt_last = last_session(exchange, interval, Calendar.from_timestamp(path.stat().st_mtime))
        now_dt_last = last_session(exchange, interval, Calendar.utc_now())
        return path_dt_last >= now_dt_last
    return False


def time_slices(dt_from: datetime, dt_to: datetime, interval: timedelta, size: int):
    start = dt_from
    delta = interval * size
    while start + interval <= dt_to:
        yield start + interval, min(start + delta, dt_to)
        start += delta


def transpose(items: Iterable[Clazz], keys: Iterable[str]) -> Tuple[List, ...]:
    dt = defaultdict(list)
    for i in items:
        for k in keys:
            dt[k].append(i.get(k))
    return tuple(dt[k] for k in keys)


def catch_exception(logger: logging.Logger):
    def decorator(function):

        def wrapper(*args, **kwargs):
            result = None
            try:
                result = function(*args, **kwargs)
            except KeyboardInterrupt:
                logger.info(f'{function.__name__} interrupted')
            except:
                logger.exception(f'{function.__name__} failed')
            else:
                logger.info(f'{function.__name__} done')
            return result

        wrapper.__name__ = function.__name__
        return wrapper

    return decorator
