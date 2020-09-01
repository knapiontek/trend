import sys
import time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Iterable, Tuple, Union

INTERVAL_1H = timedelta(hours=1)
INTERVAL_1D = timedelta(days=1)
INTERVAL_1W = timedelta(days=7)


def interval_name(interval: timedelta) -> str:
    return {
        INTERVAL_1H: '1h',
        INTERVAL_1D: '1d',
        INTERVAL_1W: '1w'
    }[interval]


def last_sunday(dt: datetime):
    d = dt.toordinal()
    return datetime.fromordinal(d - (d % 7))


def dt_round(dt: datetime, interval: timedelta) -> datetime:
    return {
        INTERVAL_1H: lambda: dt.replace(minute=0, second=0, microsecond=0),
        INTERVAL_1D: lambda: dt.replace(hour=0, minute=0, second=0, microsecond=0),
        INTERVAL_1W: last_sunday
    }[interval]()


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def from_ts_ms(ts: int, tz: timezone) -> datetime:
    return datetime.fromtimestamp(ts / 1000, tz=tz)


def to_ts_ms(dt: datetime) -> int:
    return int(time.mktime(dt.utctimetuple()) * 1000 + dt.microsecond / 1000)


UTC_TZ = timezone(timedelta(hours=0), 'GMT')
DUBLIN_TZ = timezone(timedelta(hours=1), 'GMT')
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


def time_slices(dt_from: datetime, dt_to: datetime, delta: timedelta, interval: timedelta):
    assert interval < delta
    start = dt_from
    while start + interval < dt_to:
        yield start + interval, min(start + delta, dt_to)
        start += delta


def transpose(lst: Iterable[Dict], keys: Iterable[str]) -> Dict[str, List]:
    dt = defaultdict(list)
    for i in lst:
        for k in keys:
            dt[k].append(i[k])
    return dt


def tuple_it(data: Union[Dict, Iterable[Dict]], keys: Iterable[str]) -> Iterable[Tuple]:
    if isinstance(data, Dict):
        schema = data['schema']
        indices = [schema.index(c) for c in keys]
        for datum in data['data']:
            yield tuple([datum[i] for i in indices])
    elif isinstance(data, Iterable):
        for i in data:
            yield tuple([i[k] for k in keys])


def dict_it(data: Union[Dict, Iterable[Dict]], keys: Iterable[str]) -> Iterable[Dict]:
    if isinstance(data, Dict):
        schema = data['schema']
        indices = [schema.index(c) for c in keys]
        for datum in data['data']:
            yield {schema[i]: datum[i] for i in indices}
    elif isinstance(data, Iterable):
        for i in data:
            yield {k: i[k] for k in keys}


class Progress:
    def __init__(self, message: str, length: int):
        self.count = 0
        self.message = message
        self.length = length

    def __add__(self, i: int):
        self.count += i
        sys.stdout.write(f'\r{self.message}: {100 * self.count / self.length:.1f}%')
        if self.count == self.length:
            sys.stdout.write('\n')
        sys.stdout.flush()
        return self
