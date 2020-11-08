import logging
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Iterable, Tuple, Set, Any

from src import holidays


class Clazz(dict):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __getattr__(self, key):
        return super().__getitem__(key)

    def __setattr__(self, key, value):
        return super().__setitem__(key, value)

    def from_dict(self, dt: Dict) -> 'Clazz':
        self.__dict__.update(dt)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return dict(self)


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def symbol_split(symbol: str) -> Tuple[str, str]:
    parts = symbol.split('.')
    return '.'.join(parts[:-1]), parts[-1]


def module_name(name: str) -> str:
    return name.split('.')[-1]


def from_timestamp(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def to_timestamp(dt: datetime) -> int:
    assert dt.tzinfo
    return int(dt.timestamp())


def utc_now():
    return datetime.now(tz=timezone.utc)


DT_FORMAT = '%Y-%m-%d %H:%M:%S %z'
D_FORMAT = '%Y-%m-%d'


def dt_parse(dt: str):
    return datetime.strptime(dt, DT_FORMAT).replace(tzinfo=timezone.utc)


def d_parse(dt: str):
    return datetime.strptime(dt, D_FORMAT).replace(tzinfo=timezone.utc)


def dt_format(dt: datetime):
    return dt.strftime(DT_FORMAT)


def ts_format(ts: int):
    dt = from_timestamp(ts)
    return dt_format(dt)


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
    return {dt_parse(d) for d in holidays.EXCHANGE_HOLIDAYS[exchange]}


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


def dt_last(exchange: str, interval: timedelta, dt: datetime) -> datetime:
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
        dt = from_timestamp(path.stat().st_mtime)
        path_dt_last = dt_last(exchange, interval, dt)
        now_dt_last = dt_last(exchange, interval, utc_now())
        return path_dt_last >= now_dt_last
    return False


def time_slices(dt_from: datetime, dt_to: datetime, interval: timedelta, size: int):
    start = dt_from
    delta = interval * size
    while start + interval <= dt_to:
        yield start + interval, min(start + delta, dt_to)
        start += delta


def transpose(items: Iterable[Clazz], keys: Iterable[str]) -> Dict[str, List]:
    dt = defaultdict(list)
    for i in items:
        for k in keys:
            dt[k].append(i[k])
    return dt


def catch_exception(logger: logging.Logger):
    def decorator(function):

        def wrapper(*args, **kwargs):
            result = None
            try:
                result = function(*args, **kwargs)
            except:
                logger.exception(f'{function.__name__} has failed')
            else:
                logger.exception(f'{function.__name__} done')
            return result

        wrapper.__name__ = function.__name__
        return wrapper

    return decorator
