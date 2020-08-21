import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List

from src import config


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def from_ts_ms(ts: int, tz: timezone) -> datetime:
    return datetime.fromtimestamp(ts / 1000, tz=tz)


def to_ts_ms(dt: datetime) -> int:
    return int(time.mktime(dt.utctimetuple()) * 1000 + dt.microsecond / 1000)


def dt_format(dt: datetime):
    return dt.strftime('%Y-%m-%d %H:%M:%S%z')


def ts_format(ts: int, tz: timezone):
    dt = from_ts_ms(ts, tz)
    return dt_format(dt)


def list_split(lst: List, delta=5):
    for i in range(0, len(lst), delta):
        yield lst[i:i + delta]


def time_slices(dt_from: datetime, dt_to: datetime, delta: timedelta, duration: int):
    duration_delta = config.duration_delta(0)
    start = dt_from
    stop = start + delta
    while stop < dt_to:
        yield start + duration_delta, stop
        duration_delta = config.duration_delta(duration)
        start += delta
        stop += delta
    yield start + duration_delta, dt_to
