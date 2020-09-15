import sys
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import List, Dict, Iterable, Tuple, Union, Any, Sized


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def from_timestamp(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def to_timestamp(dt: datetime) -> int:
    assert dt.tzinfo
    return int(dt.timestamp())


def utc_now():
    return datetime.now(tz=timezone.utc)


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


INTERVAL_1H = timedelta(hours=1)
INTERVAL_1D = timedelta(days=1)
INTERVAL_1W = timedelta(days=7)


def interval_name(interval: timedelta) -> str:
    return {
        INTERVAL_1H: '1h',
        INTERVAL_1D: '1d',
        INTERVAL_1W: '1w'
    }[interval]


EXCHANGE_HOLIDAYS = {
    'NYSE': {
        '2018-01-01 00:00:00+0000',
        '2018-01-15 00:00:00+0000',
        '2018-02-19 00:00:00+0000',
        '2018-03-30 00:00:00+0000',
        '2018-05-28 00:00:00+0000',
        '2018-07-04 00:00:00+0000',
        '2018-09-03 00:00:00+0000',
        '2018-11-22 00:00:00+0000',
        "2018-12-05 00:00:00+0000",
        '2018-12-25 00:00:00+0000',

        '2019-01-01 00:00:00+0000',
        '2019-01-21 00:00:00+0000',
        '2019-02-18 00:00:00+0000',
        '2019-04-19 00:00:00+0000',
        '2019-05-27 00:00:00+0000',
        '2019-07-04 00:00:00+0000',
        '2019-09-02 00:00:00+0000',
        '2019-11-28 00:00:00+0000',
        '2019-12-25 00:00:00+0000',

        '2020-01-01 00:00:00+0000',
        '2020-01-20 00:00:00+0000',
        '2020-02-17 00:00:00+0000',
        '2020-04-10 00:00:00+0000',
        '2020-05-25 00:00:00+0000',
        '2020-07-03 00:00:00+0000',
        '2020-09-07 00:00:00+0000',
        '2020-11-26 00:00:00+0000',
        '2020-12-25 00:00:00+0000',

        '2021-01-01 00:00:00+0000',
        '2021-01-18 00:00:00+0000',
        '2021-02-15 00:00:00+0000',
        '2021-04-02 00:00:00+0000',
        '2021-05-31 00:00:00+0000',
        '2021-07-05 00:00:00+0000',
        '2021-09-06 00:00:00+0000',
        '2021-11-25 00:00:00+0000',
        '2021-12-24 00:00:00+0000',

        '2022-01-01 00:00:00+0000',
        '2022-01-17 00:00:00+0000',
        '2022-02-21 00:00:00+0000',
        '2022-04-15 00:00:00+0000',
        '2022-05-30 00:00:00+0000',
        '2022-07-04 00:00:00+0000',
        '2022-09-05 00:00:00+0000',
        '2022-11-24 00:00:00+0000',
        '2022-12-26 00:00:00+0000'
    },
    'NASDAQ': {
        '2018-01-01 00:00:00+0000',
        '2018-01-15 00:00:00+0000',
        '2018-02-19 00:00:00+0000',
        '2018-03-30 00:00:00+0000',
        '2018-05-28 00:00:00+0000',
        '2018-07-04 00:00:00+0000',
        '2018-09-03 00:00:00+0000',
        '2018-11-22 00:00:00+0000',
        "2018-12-05 00:00:00+0000",
        '2018-12-25 00:00:00+0000',

        '2019-01-01 00:00:00+0000',
        '2019-01-21 00:00:00+0000',
        '2019-02-18 00:00:00+0000',
        '2019-04-19 00:00:00+0000',
        '2019-05-27 00:00:00+0000',
        '2019-07-04 00:00:00+0000',
        '2019-09-02 00:00:00+0000',
        '2019-11-28 00:00:00+0000',
        '2019-12-25 00:00:00+0000',

        '2020-01-01 00:00:00+0000',
        '2020-01-20 00:00:00+0000',
        '2020-02-17 00:00:00+0000',
        '2020-04-10 00:00:00+0000',
        '2020-05-25 00:00:00+0000',
        '2020-07-03 00:00:00+0000',
        '2020-09-07 00:00:00+0000',
        '2020-11-26 00:00:00+0000',
        '2020-12-25 00:00:00+0000',

        '2021-01-01 00:00:00+0000',
        '2021-01-18 00:00:00+0000',
        '2021-02-15 00:00:00+0000',
        '2021-04-02 00:00:00+0000',
        '2021-05-31 00:00:00+0000',
        '2021-07-05 00:00:00+0000',
        '2021-09-06 00:00:00+0000',
        '2021-11-25 00:00:00+0000',
        '2021-12-24 00:00:00+0000',

        '2022-01-01 00:00:00+0000',
        '2022-01-17 00:00:00+0000',
        '2022-02-21 00:00:00+0000',
        '2022-04-15 00:00:00+0000',
        '2022-05-30 00:00:00+0000',
        '2022-07-04 00:00:00+0000',
        '2022-09-05 00:00:00+0000',
        '2022-11-24 00:00:00+0000',
        '2022-12-26 00:00:00+0000'
    }
}


@lru_cache(maxsize=16)
def holidays(exchange: str):
    return {dt_parse(d) for d in EXCHANGE_HOLIDAYS[exchange]}


def last_workday(exchange: str, dt=utc_now()) -> datetime:
    exchange_holidays = holidays(exchange)
    d = dt.toordinal()
    while True:
        d -= 1
        day = datetime.fromordinal(d)
        day = day.replace(tzinfo=timezone.utc)
        if day.weekday() in (0, 1, 2, 3, 4) and day not in exchange_holidays:
            return day


def last_sunday(dt=utc_now()) -> datetime:
    d = dt.toordinal()
    return datetime.fromordinal(d - (d % 7)).replace(tzinfo=timezone.utc)


def dt_last(exchange: str, interval: timedelta) -> datetime:
    """
    It returns datetime where all fields smaller than interval are set to zero.
    It is up to a data driver to modify it to meet a provider requirements.
    """
    if interval == INTERVAL_1H:
        return utc_now().replace(minute=0, second=0, microsecond=0)
    if interval == INTERVAL_1D:
        return last_workday(exchange)
    if interval == INTERVAL_1W:
        return last_sunday()


def time_slices(dt_from: datetime, dt_to: datetime, interval: timedelta, size: int):
    start = dt_from
    delta = interval * size
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
