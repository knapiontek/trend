import logging
import math as _math
import time as _time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone, date, time
from functools import lru_cache
from pathlib import Path
from typing import List, Iterable, Tuple, Set, Union, Any

from src import holidays
from src.clazz import Clazz

DT_FORMAT = '%Y-%m-%d %H:%M:%S'
D_FORMAT = '%Y-%m-%d'


class DateTime(datetime):

    def __new__(cls, year, month=None, day=None, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0):
        return super().__new__(cls, year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)

    def __add__(self, other):
        """Override buggy original function"""
        if not isinstance(other, timedelta):
            return NotImplemented
        delta = timedelta(self.toordinal(),
                          hours=self.hour,
                          minutes=self.minute,
                          seconds=self.second,
                          microseconds=self.microsecond)
        delta += other
        hour, rem = divmod(delta.seconds, 3600)
        minute, second = divmod(rem, 60)
        if 0 < delta.days <= date.max.toordinal():
            return self.combine(date.fromordinal(delta.days),
                                time(hour, minute, second, delta.microseconds, tzinfo=self.tzinfo))
        raise OverflowError("result out of range")

    __radd__ = __add__

    def __repr__(self):
        return f'{self.__class__.__qualname__}({self.format()})'

    def __str__(self):
        return self.format()

    def to_timestamp(self) -> int:
        assert self.tzinfo
        return int(self.timestamp())

    @classmethod
    def from_timestamp(cls, ts: Union[int, float]) -> 'DateTime':
        """Override buggy original function"""
        fraction, t = _math.modf(ts)
        us = round(fraction * 1e6)
        if us >= 1000000:
            t += 1
            us -= 1000000
        elif us < 0:
            t -= 1
            us += 1000000
        year, month, day, hour, minute, second, _, _, _ = _time.gmtime(t)
        second = min(second, 59)
        return cls(year, month, day, hour, minute, second, us, timezone.utc)

    @classmethod
    def now(cls) -> 'DateTime':
        ts = _time.time()
        return cls.from_timestamp(ts)

    @classmethod
    def parse_datetime(cls, dt: str) -> 'DateTime':
        return cls.strptime(dt, DT_FORMAT).replace(tzinfo=timezone.utc)

    @classmethod
    def parse_date(cls, d: str) -> 'DateTime':
        return cls.strptime(d, D_FORMAT).replace(tzinfo=timezone.utc)

    def format(self) -> str:
        return self.strftime(DT_FORMAT)


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def symbol_split(symbol: str) -> Tuple[str, str]:
    parts = symbol.split('.')
    return '.'.join(parts[:-1]), parts[-1]


INTERVAL_1H = timedelta(hours=1)
INTERVAL_1D = timedelta(days=1)
INTERVAL_1W = timedelta(days=7)


def interval_name(interval: timedelta) -> str:
    return {
        INTERVAL_1H: '1h',
        INTERVAL_1D: '1d',
        INTERVAL_1W: '1w'
    }[interval]


def source_name(engine: Any, interval: Union[timedelta, str]) -> str:
    if not isinstance(engine, str):
        engine = engine.__name__
    engine_name = engine.split('.')[-1]
    if isinstance(interval, timedelta):
        interval = interval_name(interval)
    return f'{engine_name}_{interval}'


ENV_TEST = 'test'
ENV_LIVE = 'live'


def result_name(engine: Any, interval: Union[timedelta, str], env_name: str) -> str:
    source = source_name(engine, interval)
    return f'{source}_{env_name}'


def health_name(engine: Any, interval: Union[timedelta, str]) -> str:
    source = source_name(engine, interval)
    return f'{source}_health'


@lru_cache(maxsize=16)
def exchange_holidays(exchange: str) -> Set[str]:
    return {DateTime.parse_datetime(dt) for dt in holidays.EXCHANGE_HOLIDAYS[exchange]}


def last_workday(exchange: str, dt: DateTime) -> DateTime:
    _holidays = exchange_holidays(exchange)
    d = dt.toordinal()
    while True:
        d -= 1
        day = DateTime.fromordinal(d)
        day = day.replace(tzinfo=timezone.utc)
        if day.weekday() in (0, 1, 2, 3, 4) and day not in _holidays:
            return day


def last_sunday(dt: DateTime) -> DateTime:
    d = dt.toordinal()
    return DateTime.fromordinal(d - (d % 7)).replace(tzinfo=timezone.utc)


def last_session(exchange: str, interval: timedelta, dt: DateTime) -> DateTime:
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
        path_dt_last = last_session(exchange, interval, DateTime.from_timestamp(path.stat().st_mtime))
        now_dt_last = last_session(exchange, interval, DateTime.now())
        return path_dt_last >= now_dt_last
    return False


def time_slices(dt_from: DateTime, dt_to: DateTime, interval: timedelta, size: int):
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


def json_default(obj):
    if callable(obj):
        return obj.__name__
    elif isinstance(obj, timedelta):
        return interval_name(obj)
    elif isinstance(obj, DateTime):
        return obj.format()
