import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pprint import pprint
from typing import List

import requests

from src import config

URL = config.exante_url()
DUBLIN_TZ = timezone(timedelta(hours=1), 'GMT')


def list_split(lst: List, chunk_size=5):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def to_timestamp(dt: datetime) -> int:
    return int(time.mktime(dt.utctimetuple()) * 1000 + dt.microsecond / 1000)


def from_timestamp(ts: int) -> datetime:
    return datetime.fromtimestamp(ts / 1000, tz=DUBLIN_TZ)


DURATION_1M = 60
DURATION_5M = 5 * 60
DURATION_10M = 10 * 60
DURATION_15M = 15 * 60
DURATION_1H = 60 * 60
DURATION_6H = 6 * 60 * 60
DURATION_1D = 24 * 60 * 60


class ExanteSession(requests.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.auth = config.exante_auth()

    def symbols(self):
        response = self.get(f'{URL}/symbols')
        assert response.status_code == 200, response.text
        return response.json()

    def candles(self, symbol: str, batch_size: int, duration: int) -> List:
        seconds = batch_size * duration
        dt_to = datetime.now(tz=DUBLIN_TZ)
        dt_from = dt_to - timedelta(seconds=seconds)
        params = {
            'dt_from': dt_from.isoformat(),
            'from': to_timestamp(dt_from),
            'dt_to': dt_to.isoformat(),
            'to': to_timestamp(dt_to),
            'size': 100,
            'type': 'trades'
        }
        url = f'{URL}/ohlc/{url_encode(symbol)}/{duration}'
        pprint(url)
        pprint(params)
        response = self.get(url=url, params=params)
        assert response.status_code == 200, response.text
        candles = response.json()
        for candle in candles:
            candle['datetime'] = from_timestamp(candle['timestamp']).isoformat()
        pprint(candles)
        return candles
