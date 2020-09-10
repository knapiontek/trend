import sys
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Iterable, Tuple, Union, Any, Sized

INTERVAL_1H = timedelta(hours=1)
INTERVAL_1D = timedelta(days=1)
INTERVAL_1W = timedelta(days=7)


def interval_name(interval: timedelta) -> str:
    return {
        INTERVAL_1H: '1h',
        INTERVAL_1D: '1d',
        INTERVAL_1W: '1w'
    }[interval]


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def last_sunday(dt: datetime):
    d = dt.toordinal()
    return datetime.fromordinal(d - (d % 7))


def utc_now():
    return datetime.now(tz=timezone.utc)


def dt_round(dt: datetime, interval: timedelta) -> datetime:
    return {
        INTERVAL_1H: lambda _dt: _dt.replace(minute=0, second=0, microsecond=0),
        INTERVAL_1D: lambda _dt: _dt.replace(hour=0, minute=0, second=0, microsecond=0),
        INTERVAL_1W: last_sunday
    }[interval](dt)


def from_timestamp(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def to_timestamp(dt: datetime) -> int:
    assert dt.tzinfo
    return int(dt.timestamp())


DT_FORMAT = '%Y-%m-%d %H:%M:%S%z'


def dt_parse(dt: str):
    return datetime.strptime(dt, DT_FORMAT)


def dt_format(dt: datetime):
    return dt.strftime(DT_FORMAT)


def ts_format(ts: int):
    dt = from_timestamp(ts)
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


def loop_it(data: Union[Dict, Iterable[Dict]], key: str) -> Iterable[Any]:
    if isinstance(data, Dict):
        schema = data['schema']
        index = schema.index(key)
        for datum in data['data']:
            yield datum[index]
    elif isinstance(data, Iterable):
        for datum in data:
            yield datum[key]


class Progress:
    def __init__(self, title: str, sized: Sized):
        self.count = -1
        self.title = title
        self.length = len(sized)

    def __enter__(self) -> 'Progress':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.count += 1
        sys.stdout.write(f'{self.title}: {100 * self.count / self.length:.1f}% done                                 \n')
        sys.stdout.flush()
        if not exc_type:
            assert self.count == self.length

    def __call__(self, message: str):
        self.count += 1
        sys.stdout.write(f'{self.title}: {100 * self.count / self.length:.1f}% {message}                            \r')
        sys.stdout.flush()
        return self
