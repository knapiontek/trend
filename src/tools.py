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


def list_split(lst: List, chunk_size=5):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def time_slices(since: datetime, delta: timedelta):
    start = since
    now = datetime.now(tz=config.UTC_TZ)
    while start < now:
        stop = start + delta
        yield start, stop
        start = stop
    return start, now
