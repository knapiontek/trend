import time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import List, Dict


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def from_ts_ms(ts: int, tz: timezone) -> datetime:
    return datetime.fromtimestamp(ts / 1000, tz=tz)


def to_ts_ms(dt: datetime) -> int:
    return int(time.mktime(dt.utctimetuple()) * 1000 + dt.microsecond / 1000)


DT_FORMAT = '%Y-%m-%d %H:%M:%S%z'


def dt_parse(dt: str):
    return datetime.strptime(dt, DT_FORMAT)


def dt_format(dt: datetime):
    return dt.strftime(DT_FORMAT)


def ts_format(ts: int, tz: timezone):
    dt = from_ts_ms(ts, tz)
    return dt_format(dt)


def list_split(lst: List, delta=5):
    for i in range(0, len(lst), delta):
        yield lst[i:i + delta]


def time_slices(dt_from: datetime, dt_to: datetime, slice_delta: timedelta, time_delta: timedelta):
    assert time_delta < slice_delta
    start = dt_from
    while start + time_delta < dt_to:
        yield start + time_delta, min(start + slice_delta, dt_to)
        start += slice_delta


def transpose(lst: List[Dict], keys: List[str]) -> Dict[str, List]:
    dt = defaultdict(list)
    for i in lst:
        for k in keys:
            dt[k].append(i[k])
    return dt
