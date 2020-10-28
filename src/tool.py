import sys
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Iterable, Tuple, Union, Any, Sized, Set

from more_itertools import windowed


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


EXCHANGE_HOLIDAYS = {
    'NYSE': {
        "2010-01-18 00:00:00 +0000",
        "2010-02-15 00:00:00 +0000",
        "2010-04-02 00:00:00 +0000",
        "2010-05-31 00:00:00 +0000",
        "2010-07-05 00:00:00 +0000",
        "2010-09-06 00:00:00 +0000",
        "2010-11-25 00:00:00 +0000",
        "2010-12-24 00:00:00 +0000",

        "2011-01-17 00:00:00 +0000",
        "2011-02-21 00:00:00 +0000",
        "2011-04-22 00:00:00 +0000",
        "2011-05-30 00:00:00 +0000",
        "2011-07-04 00:00:00 +0000",
        "2011-09-05 00:00:00 +0000",
        "2011-11-24 00:00:00 +0000",
        "2011-12-26 00:00:00 +0000",

        "2012-01-02 00:00:00 +0000",
        "2012-01-16 00:00:00 +0000",
        "2012-02-20 00:00:00 +0000",
        "2012-04-06 00:00:00 +0000",
        "2012-05-28 00:00:00 +0000",
        "2012-07-04 00:00:00 +0000",
        "2012-09-03 00:00:00 +0000",
        "2012-10-29 00:00:00 +0000",
        "2012-10-30 00:00:00 +0000",
        "2012-11-22 00:00:00 +0000",
        "2012-12-25 00:00:00 +0000",

        "2013-01-01 00:00:00 +0000",
        "2013-01-21 00:00:00 +0000",
        "2013-02-18 00:00:00 +0000",
        "2013-03-29 00:00:00 +0000",
        "2013-05-27 00:00:00 +0000",
        "2013-07-04 00:00:00 +0000",
        "2013-09-02 00:00:00 +0000",
        "2013-11-28 00:00:00 +0000",
        "2013-12-25 00:00:00 +0000",

        "2014-01-01 00:00:00 +0000",
        "2014-01-20 00:00:00 +0000",
        "2014-02-17 00:00:00 +0000",
        "2014-04-18 00:00:00 +0000",
        "2014-05-26 00:00:00 +0000",
        "2014-07-04 00:00:00 +0000",
        "2014-09-01 00:00:00 +0000",
        "2014-11-27 00:00:00 +0000",
        "2014-12-25 00:00:00 +0000",

        "2015-01-01 00:00:00 +0000",
        "2015-01-19 00:00:00 +0000",
        "2015-02-16 00:00:00 +0000",
        "2015-04-03 00:00:00 +0000",
        "2015-05-25 00:00:00 +0000",
        "2015-07-03 00:00:00 +0000",
        "2015-09-07 00:00:00 +0000",
        "2015-11-26 00:00:00 +0000",
        "2015-12-25 00:00:00 +0000",

        "2016-01-01 00:00:00 +0000",
        "2016-01-18 00:00:00 +0000",
        "2016-02-15 00:00:00 +0000",
        "2016-03-25 00:00:00 +0000",
        "2016-05-30 00:00:00 +0000",
        "2016-07-04 00:00:00 +0000",
        "2016-09-05 00:00:00 +0000",
        "2016-11-24 00:00:00 +0000",
        "2016-12-26 00:00:00 +0000",

        "2017-01-02 00:00:00 +0000",
        "2017-01-16 00:00:00 +0000",
        "2017-02-20 00:00:00 +0000",
        "2017-04-14 00:00:00 +0000",
        "2017-05-29 00:00:00 +0000",
        "2017-07-04 00:00:00 +0000",
        "2017-09-04 00:00:00 +0000",
        "2017-11-23 00:00:00 +0000",
        "2017-12-25 00:00:00 +0000",

        '2018-01-01 00:00:00 +0000',
        '2018-01-15 00:00:00 +0000',
        '2018-02-19 00:00:00 +0000',
        '2018-03-30 00:00:00 +0000',
        '2018-05-28 00:00:00 +0000',
        '2018-07-04 00:00:00 +0000',
        '2018-09-03 00:00:00 +0000',
        '2018-11-22 00:00:00 +0000',
        '2018-12-05 00:00:00 +0000',
        '2018-12-25 00:00:00 +0000',

        '2019-01-01 00:00:00 +0000',
        '2019-01-21 00:00:00 +0000',
        '2019-02-18 00:00:00 +0000',
        '2019-04-19 00:00:00 +0000',
        '2019-05-27 00:00:00 +0000',
        '2019-07-04 00:00:00 +0000',
        '2019-09-02 00:00:00 +0000',
        '2019-11-28 00:00:00 +0000',
        '2019-12-25 00:00:00 +0000',

        '2020-01-01 00:00:00 +0000',
        '2020-01-20 00:00:00 +0000',
        '2020-02-17 00:00:00 +0000',
        '2020-04-10 00:00:00 +0000',
        '2020-05-25 00:00:00 +0000',
        '2020-07-03 00:00:00 +0000',
        '2020-09-07 00:00:00 +0000',
        '2020-11-26 00:00:00 +0000',
        '2020-12-25 00:00:00 +0000',

        '2021-01-01 00:00:00 +0000',
        '2021-01-18 00:00:00 +0000',
        '2021-02-15 00:00:00 +0000',
        '2021-04-02 00:00:00 +0000',
        '2021-05-31 00:00:00 +0000',
        '2021-07-05 00:00:00 +0000',
        '2021-09-06 00:00:00 +0000',
        '2021-11-25 00:00:00 +0000',
        '2021-12-24 00:00:00 +0000',

        '2022-01-01 00:00:00 +0000',
        '2022-01-17 00:00:00 +0000',
        '2022-02-21 00:00:00 +0000',
        '2022-04-15 00:00:00 +0000',
        '2022-05-30 00:00:00 +0000',
        '2022-07-04 00:00:00 +0000',
        '2022-09-05 00:00:00 +0000',
        '2022-11-24 00:00:00 +0000',
        '2022-12-26 00:00:00 +0000'
    },
    'NASDAQ': {
        "2010-01-18 00:00:00 +0000",
        "2010-02-15 00:00:00 +0000",
        "2010-04-02 00:00:00 +0000",
        "2010-05-31 00:00:00 +0000",
        "2010-07-05 00:00:00 +0000",
        "2010-09-06 00:00:00 +0000",
        "2010-11-25 00:00:00 +0000",
        "2010-12-24 00:00:00 +0000",

        "2011-01-17 00:00:00 +0000",
        "2011-02-21 00:00:00 +0000",
        "2011-04-22 00:00:00 +0000",
        "2011-05-30 00:00:00 +0000",
        "2011-07-04 00:00:00 +0000",
        "2011-09-05 00:00:00 +0000",
        "2011-11-24 00:00:00 +0000",
        "2011-12-26 00:00:00 +0000",

        "2012-01-02 00:00:00 +0000",
        "2012-01-16 00:00:00 +0000",
        "2012-02-20 00:00:00 +0000",
        "2012-04-06 00:00:00 +0000",
        "2012-05-28 00:00:00 +0000",
        "2012-07-04 00:00:00 +0000",
        "2012-09-03 00:00:00 +0000",
        "2012-10-29 00:00:00 +0000",
        "2012-10-30 00:00:00 +0000",
        "2012-11-22 00:00:00 +0000",
        "2012-12-25 00:00:00 +0000",

        "2013-01-01 00:00:00 +0000",
        "2013-01-21 00:00:00 +0000",
        "2013-02-18 00:00:00 +0000",
        "2013-03-29 00:00:00 +0000",
        "2013-05-27 00:00:00 +0000",
        "2013-07-04 00:00:00 +0000",
        "2013-09-02 00:00:00 +0000",
        "2013-11-28 00:00:00 +0000",
        "2013-12-25 00:00:00 +0000",

        "2014-01-01 00:00:00 +0000",
        "2014-01-20 00:00:00 +0000",
        "2014-02-17 00:00:00 +0000",
        "2014-04-18 00:00:00 +0000",
        "2014-05-26 00:00:00 +0000",
        "2014-07-04 00:00:00 +0000",
        "2014-09-01 00:00:00 +0000",
        "2014-11-27 00:00:00 +0000",
        "2014-12-25 00:00:00 +0000",

        "2015-01-01 00:00:00 +0000",
        "2015-01-19 00:00:00 +0000",
        "2015-02-16 00:00:00 +0000",
        "2015-04-03 00:00:00 +0000",
        "2015-05-25 00:00:00 +0000",
        "2015-07-03 00:00:00 +0000",
        "2015-09-07 00:00:00 +0000",
        "2015-11-26 00:00:00 +0000",
        "2015-12-25 00:00:00 +0000",

        "2016-01-01 00:00:00 +0000",
        "2016-01-18 00:00:00 +0000",
        "2016-02-15 00:00:00 +0000",
        "2016-03-25 00:00:00 +0000",
        "2016-05-30 00:00:00 +0000",
        "2016-07-04 00:00:00 +0000",
        "2016-09-05 00:00:00 +0000",
        "2016-11-24 00:00:00 +0000",
        "2016-12-26 00:00:00 +0000",

        "2017-01-02 00:00:00 +0000",
        "2017-01-16 00:00:00 +0000",
        "2017-02-20 00:00:00 +0000",
        "2017-04-14 00:00:00 +0000",
        "2017-05-29 00:00:00 +0000",
        "2017-07-04 00:00:00 +0000",
        "2017-09-04 00:00:00 +0000",
        "2017-11-23 00:00:00 +0000",
        "2017-12-25 00:00:00 +0000",

        '2018-01-01 00:00:00 +0000',
        '2018-01-15 00:00:00 +0000',
        '2018-02-19 00:00:00 +0000',
        '2018-03-30 00:00:00 +0000',
        '2018-05-28 00:00:00 +0000',
        '2018-07-04 00:00:00 +0000',
        '2018-09-03 00:00:00 +0000',
        '2018-11-22 00:00:00 +0000',
        '2018-12-05 00:00:00 +0000',
        '2018-12-25 00:00:00 +0000',

        '2019-01-01 00:00:00 +0000',
        '2019-01-21 00:00:00 +0000',
        '2019-02-18 00:00:00 +0000',
        '2019-04-19 00:00:00 +0000',
        '2019-05-27 00:00:00 +0000',
        '2019-07-04 00:00:00 +0000',
        '2019-09-02 00:00:00 +0000',
        '2019-11-28 00:00:00 +0000',
        '2019-12-25 00:00:00 +0000',

        '2020-01-01 00:00:00 +0000',
        '2020-01-20 00:00:00 +0000',
        '2020-02-17 00:00:00 +0000',
        '2020-04-10 00:00:00 +0000',
        '2020-05-25 00:00:00 +0000',
        '2020-07-03 00:00:00 +0000',
        '2020-09-07 00:00:00 +0000',
        '2020-11-26 00:00:00 +0000',
        '2020-12-25 00:00:00 +0000',

        '2021-01-01 00:00:00 +0000',
        '2021-01-18 00:00:00 +0000',
        '2021-02-15 00:00:00 +0000',
        '2021-04-02 00:00:00 +0000',
        '2021-05-31 00:00:00 +0000',
        '2021-07-05 00:00:00 +0000',
        '2021-09-06 00:00:00 +0000',
        '2021-11-25 00:00:00 +0000',
        '2021-12-24 00:00:00 +0000',

        '2022-01-01 00:00:00 +0000',
        '2022-01-17 00:00:00 +0000',
        '2022-02-21 00:00:00 +0000',
        '2022-04-15 00:00:00 +0000',
        '2022-05-30 00:00:00 +0000',
        '2022-07-04 00:00:00 +0000',
        '2022-09-05 00:00:00 +0000',
        '2022-11-24 00:00:00 +0000',
        '2022-12-26 00:00:00 +0000'
    },
    'LSE': {
        "2010-04-02 00:00:00 +0000",
        "2010-04-05 00:00:00 +0000",
        "2010-05-03 00:00:00 +0000",
        "2010-05-31 00:00:00 +0000",
        "2010-08-30 00:00:00 +0000",
        "2010-12-27 00:00:00 +0000",
        "2010-12-28 00:00:00 +0000",

        "2011-01-03 00:00:00 +0000",
        "2011-04-22 00:00:00 +0000",
        "2011-04-25 00:00:00 +0000",
        "2011-04-29 00:00:00 +0000",
        "2011-05-02 00:00:00 +0000",
        "2011-05-30 00:00:00 +0000",
        "2011-08-29 00:00:00 +0000",
        "2011-12-26 00:00:00 +0000",
        "2011-12-27 00:00:00 +0000",

        "2012-01-02 00:00:00 +0000",
        "2012-04-06 00:00:00 +0000",
        "2012-04-09 00:00:00 +0000",
        "2012-05-07 00:00:00 +0000",
        "2012-06-04 00:00:00 +0000",
        "2012-06-05 00:00:00 +0000",
        "2012-08-27 00:00:00 +0000",
        "2012-12-25 00:00:00 +0000",
        "2012-12-26 00:00:00 +0000",

        "2013-01-01 00:00:00 +0000",
        "2013-03-29 00:00:00 +0000",
        "2013-04-01 00:00:00 +0000",
        "2013-05-06 00:00:00 +0000",
        "2013-05-27 00:00:00 +0000",
        "2013-08-26 00:00:00 +0000",
        "2013-12-25 00:00:00 +0000",
        "2013-12-26 00:00:00 +0000",

        "2014-01-01 00:00:00 +0000",
        "2014-04-18 00:00:00 +0000",
        "2014-04-21 00:00:00 +0000",
        "2014-05-05 00:00:00 +0000",
        "2014-05-26 00:00:00 +0000",
        "2014-08-25 00:00:00 +0000",
        "2014-12-25 00:00:00 +0000",
        "2014-12-26 00:00:00 +0000",

        "2015-01-01 00:00:00 +0000",
        "2015-04-03 00:00:00 +0000",
        "2015-04-06 00:00:00 +0000",
        "2015-05-04 00:00:00 +0000",
        "2015-05-25 00:00:00 +0000",
        "2015-08-31 00:00:00 +0000",
        "2015-12-25 00:00:00 +0000",
        "2015-12-28 00:00:00 +0000",

        "2016-01-01 00:00:00 +0000",
        "2016-03-25 00:00:00 +0000",
        "2016-03-28 00:00:00 +0000",
        "2016-05-02 00:00:00 +0000",
        "2016-05-30 00:00:00 +0000",
        "2016-08-29 00:00:00 +0000",
        "2016-12-26 00:00:00 +0000",
        "2016-12-27 00:00:00 +0000",

        "2017-01-02 00:00:00 +0000",
        "2017-04-14 00:00:00 +0000",
        "2017-04-17 00:00:00 +0000",
        "2017-05-01 00:00:00 +0000",
        "2017-05-29 00:00:00 +0000",
        "2017-08-28 00:00:00 +0000",
        "2017-12-25 00:00:00 +0000",
        "2017-12-26 00:00:00 +0000",

        "2018-03-30 00:00:00 +0000",
        "2018-04-02 00:00:00 +0000",
        "2018-05-07 00:00:00 +0000",
        "2018-05-28 00:00:00 +0000",
        "2018-08-27 00:00:00 +0000",
        "2018-12-25 00:00:00 +0000",
        "2018-12-26 00:00:00 +0000",

        "2019-01-01 00:00:00 +0000",
        "2019-04-19 00:00:00 +0000",
        "2019-04-22 00:00:00 +0000",
        "2019-05-06 00:00:00 +0000",
        "2019-05-27 00:00:00 +0000",
        "2019-08-26 00:00:00 +0000",
        "2019-12-25 00:00:00 +0000",
        "2019-12-26 00:00:00 +0000",

        "2020-01-01 00:00:00 +0000",
        "2020-04-10 00:00:00 +0000",
        "2020-04-13 00:00:00 +0000",
        "2020-05-08 00:00:00 +0000",
        "2020-05-25 00:00:00 +0000",
        "2020-08-31 00:00:00 +0000"
    },
    'XETRA': {
        "2010-04-02 00:00:00 +0000",
        "2010-04-05 00:00:00 +0000",
        "2010-12-24 00:00:00 +0000",
        "2010-12-31 00:00:00 +0000",
        "2011-04-22 00:00:00 +0000",
        "2011-04-25 00:00:00 +0000",
        "2011-12-26 00:00:00 +0000",

        "2012-04-06 00:00:00 +0000",
        "2012-04-09 00:00:00 +0000",
        "2012-05-01 00:00:00 +0000",
        "2012-12-24 00:00:00 +0000",
        "2012-12-25 00:00:00 +0000",
        "2012-12-26 00:00:00 +0000",
        "2012-12-31 00:00:00 +0000",

        "2013-01-01 00:00:00 +0000",
        "2013-03-29 00:00:00 +0000",
        "2013-04-01 00:00:00 +0000",
        "2013-05-01 00:00:00 +0000",
        "2013-12-24 00:00:00 +0000",
        "2013-12-25 00:00:00 +0000",
        "2013-12-26 00:00:00 +0000",
        "2013-12-31 00:00:00 +0000",

        "2014-01-01 00:00:00 +0000",
        "2014-04-18 00:00:00 +0000",
        "2014-04-21 00:00:00 +0000",
        "2014-05-01 00:00:00 +0000",
        "2014-10-03 00:00:00 +0000",
        "2014-12-24 00:00:00 +0000",
        "2014-12-25 00:00:00 +0000",
        "2014-12-26 00:00:00 +0000",
        "2014-12-31 00:00:00 +0000",

        "2015-01-01 00:00:00 +0000",
        "2015-04-03 00:00:00 +0000",
        "2015-04-06 00:00:00 +0000",
        "2015-05-01 00:00:00 +0000",
        "2015-05-25 00:00:00 +0000",
        "2015-12-24 00:00:00 +0000",
        "2015-12-25 00:00:00 +0000",
        "2015-12-31 00:00:00 +0000",

        "2016-01-01 00:00:00 +0000",
        "2016-03-25 00:00:00 +0000",
        "2016-03-28 00:00:00 +0000",
        "2016-05-16 00:00:00 +0000",
        "2016-10-03 00:00:00 +0000",
        "2016-12-26 00:00:00 +0000",

        "2017-04-14 00:00:00 +0000",
        "2017-04-17 00:00:00 +0000",
        "2017-05-01 00:00:00 +0000",
        "2017-06-05 00:00:00 +0000",
        "2017-10-03 00:00:00 +0000",
        "2017-10-31 00:00:00 +0000",
        "2017-12-25 00:00:00 +0000",
        "2017-12-26 00:00:00 +0000",

        "2018-03-30 00:00:00 +0000",
        "2018-04-02 00:00:00 +0000",
        "2018-05-01 00:00:00 +0000",
        "2018-05-21 00:00:00 +0000",
        "2018-10-03 00:00:00 +0000",
        "2018-12-24 00:00:00 +0000",
        "2018-12-25 00:00:00 +0000",
        "2018-12-26 00:00:00 +0000",
        "2018-12-31 00:00:00 +0000",

        "2019-01-01 00:00:00 +0000",
        "2019-03-18 00:00:00 +0000",
        "2019-04-19 00:00:00 +0000",
        "2019-04-22 00:00:00 +0000",
        "2019-05-01 00:00:00 +0000",
        "2019-06-10 00:00:00 +0000",
        "2019-10-03 00:00:00 +0000",
        "2019-12-24 00:00:00 +0000",
        "2019-12-25 00:00:00 +0000",
        "2019-12-26 00:00:00 +0000",
        "2019-12-31 00:00:00 +0000",

        "2020-01-01 00:00:00 +0000",
        "2020-04-10 00:00:00 +0000",
        "2020-04-13 00:00:00 +0000",
        "2020-05-01 00:00:00 +0000",
        "2020-06-01 00:00:00 +0000"
    },
    'WSE': {
        "2010-04-02 00:00:00 +0000",
        "2010-04-05 00:00:00 +0000",
        "2010-05-03 00:00:00 +0000",
        "2010-06-03 00:00:00 +0000",
        "2010-11-01 00:00:00 +0000",
        "2010-11-11 00:00:00 +0000",
        "2010-12-24 00:00:00 +0000",

        "2011-01-06 00:00:00 +0000",
        "2011-04-22 00:00:00 +0000",
        "2011-04-25 00:00:00 +0000",
        "2011-05-03 00:00:00 +0000",
        "2011-06-23 00:00:00 +0000",
        "2011-08-15 00:00:00 +0000",
        "2011-11-01 00:00:00 +0000",
        "2011-11-11 00:00:00 +0000",
        "2011-12-26 00:00:00 +0000",

        "2012-01-06 00:00:00 +0000",
        "2012-04-06 00:00:00 +0000",
        "2012-04-09 00:00:00 +0000",
        "2012-05-01 00:00:00 +0000",
        "2012-05-03 00:00:00 +0000",
        "2012-06-07 00:00:00 +0000",
        "2012-08-15 00:00:00 +0000",
        "2012-11-01 00:00:00 +0000",
        "2012-12-24 00:00:00 +0000",
        "2012-12-25 00:00:00 +0000",
        "2012-12-26 00:00:00 +0000",
        "2012-12-31 00:00:00 +0000",

        "2013-01-01 00:00:00 +0000",
        "2013-03-29 00:00:00 +0000",
        "2013-04-01 00:00:00 +0000",
        "2013-04-16 00:00:00 +0000",
        "2013-05-01 00:00:00 +0000",
        "2013-05-03 00:00:00 +0000",
        "2013-05-30 00:00:00 +0000",
        "2013-08-15 00:00:00 +0000",
        "2013-11-01 00:00:00 +0000",
        "2013-11-11 00:00:00 +0000",
        "2013-12-24 00:00:00 +0000",
        "2013-12-25 00:00:00 +0000",
        "2013-12-26 00:00:00 +0000",
        "2013-12-31 00:00:00 +0000",

        "2014-01-01 00:00:00 +0000",
        "2014-01-06 00:00:00 +0000",
        "2014-04-18 00:00:00 +0000",
        "2014-04-21 00:00:00 +0000",
        "2014-05-01 00:00:00 +0000",
        "2014-06-19 00:00:00 +0000",
        "2014-08-15 00:00:00 +0000",
        "2014-11-11 00:00:00 +0000",
        "2014-12-24 00:00:00 +0000",
        "2014-12-25 00:00:00 +0000",
        "2014-12-26 00:00:00 +0000",
        "2014-12-31 00:00:00 +0000",

        "2015-01-01 00:00:00 +0000",
        "2015-01-06 00:00:00 +0000",
        "2015-04-03 00:00:00 +0000",
        "2015-04-06 00:00:00 +0000",
        "2015-05-01 00:00:00 +0000",
        "2015-06-04 00:00:00 +0000",
        "2015-11-11 00:00:00 +0000",
        "2015-12-24 00:00:00 +0000",
        "2015-12-25 00:00:00 +0000",
        "2015-12-31 00:00:00 +0000",

        "2016-01-01 00:00:00 +0000",
        "2016-01-06 00:00:00 +0000",
        "2016-03-25 00:00:00 +0000",
        "2016-03-28 00:00:00 +0000",
        "2016-05-03 00:00:00 +0000",
        "2016-05-26 00:00:00 +0000",
        "2016-08-15 00:00:00 +0000",
        "2016-11-01 00:00:00 +0000",
        "2016-11-11 00:00:00 +0000",
        "2016-12-26 00:00:00 +0000",

        "2017-01-06 00:00:00 +0000",
        "2017-04-14 00:00:00 +0000",
        "2017-04-17 00:00:00 +0000",
        "2017-05-01 00:00:00 +0000",
        "2017-05-03 00:00:00 +0000",
        "2017-06-15 00:00:00 +0000",
        "2017-08-15 00:00:00 +0000",
        "2017-11-01 00:00:00 +0000",
        "2017-12-25 00:00:00 +0000",
        "2017-12-26 00:00:00 +0000",

        '2018-03-30 00:00:00 +0000',
        '2018-04-02 00:00:00 +0000',
        '2018-05-01 00:00:00 +0000',
        '2018-05-03 00:00:00 +0000',
        '2018-05-31 00:00:00 +0000',
        '2018-08-15 00:00:00 +0000',
        '2018-11-01 00:00:00 +0000',
        '2018-11-12 00:00:00 +0000',
        '2018-12-24 00:00:00 +0000',
        '2018-12-25 00:00:00 +0000',
        '2018-12-26 00:00:00 +0000',
        '2018-12-31 00:00:00 +0000',

        '2019-01-01 00:00:00 +0000',
        '2019-04-19 00:00:00 +0000',
        '2019-04-22 00:00:00 +0000',
        '2019-05-01 00:00:00 +0000',
        '2019-05-03 00:00:00 +0000',
        '2019-06-20 00:00:00 +0000',
        '2019-08-15 00:00:00 +0000',
        '2019-11-01 00:00:00 +0000',
        '2019-11-11 00:00:00 +0000',
        '2019-12-24 00:00:00 +0000',
        '2019-12-25 00:00:00 +0000',
        '2019-12-26 00:00:00 +0000',
        '2019-12-31 00:00:00 +0000',

        '2020-01-01 00:00:00 +0000',
        '2020-01-06 00:00:00 +0000',
        '2020-04-10 00:00:00 +0000',
        '2020-04-13 00:00:00 +0000',
        '2020-05-01 00:00:00 +0000',
        '2020-06-11 00:00:00 +0000',
        '2020-11-11 00:00:00 +0000',
        '2020-12-24 00:00:00 +0000',
        '2020-12-25 00:00:00 +0000',
        '2020-12-31 00:00:00 +0000',

        '2021-01-01 00:00:00 +0000',
        '2021-01-06 00:00:00 +0000',
        '2021-04-02 00:00:00 +0000',
        '2021-04-05 00:00:00 +0000',
        '2021-05-03 00:00:00 +0000',
        '2021-06-03 00:00:00 +0000',
        '2021-11-01 00:00:00 +0000',
        '2021-11-11 00:00:00 +0000',
        '2021-12-24 00:00:00 +0000',
        '2021-12-31 00:00:00 +0000',

        '2022-01-06 00:00:00 +0000',
        '2022-04-15 00:00:00 +0000',
        '2022-04-18 00:00:00 +0000',
        '2022-05-03 00:00:00 +0000',
        '2022-06-16 00:00:00 +0000',
        '2022-08-15 00:00:00 +0000',
        '2022-11-01 00:00:00 +0000',
        '2022-12-26 00:00:00 +0000'
    }
}


@lru_cache(maxsize=16)
def holidays(exchange: str) -> Set[str]:
    return {dt_parse(d) for d in EXCHANGE_HOLIDAYS[exchange]}


def last_workday(exchange: str, dt: datetime) -> datetime:
    exchange_holidays = holidays(exchange)
    d = dt.toordinal()
    while True:
        d -= 1
        day = datetime.fromordinal(d)
        day = day.replace(tzinfo=timezone.utc)
        if day.weekday() in (0, 1, 2, 3, 4) and day not in exchange_holidays:
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


def find_gaps(series: List[datetime], interval: timedelta) -> List[datetime]:
    results = []
    for dt1, dt2 in windowed(series, 2):
        dt1 += interval
        while dt1 < dt2:
            results.append(dt1)
            dt1 += interval
    return results


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


SPACES = ' ' * 43


def print_line(message: str):
    sys.stdout.write(message)
    sys.stdout.flush()


class Progress:
    def __init__(self, title: str, size: Union[int, Sized]):
        self.count = -1
        self.title = title
        self.length = len(size) if isinstance(size, Sized) else size

    def __enter__(self) -> 'Progress':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.length:
            self.count += 1
            print_line(f'{self.title}: {100 * self.count / self.length:.1f}% done{SPACES}\n')
            if not exc_type:
                assert self.count == self.length
        else:
            print_line(f'{self.title}: done{SPACES}\n')

    def __call__(self, message: str):
        self.count += 1
        print_line(f'{self.title}: {100 * self.count / self.length:.1f}% {message}{SPACES}\r')