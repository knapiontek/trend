import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pprint import pprint
from typing import List

import requests

from src import config

URL = config.exante_url()
DUBLIN_TZ = timezone(timedelta(hours=1), 'GMT')


def url_encode(name: str) -> str:
    return urllib.parse.quote(name, safe='')


def to_timestamp(dt: datetime) -> int:
    return int(time.mktime(dt.utctimetuple()) * 1000 + dt.microsecond / 1000)


def from_timestamp(ts: int) -> datetime:
    return datetime.fromtimestamp(ts / 1000, tz=DUBLIN_TZ)


class ExanteSession(requests.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.auth = config.exante_auth()

    def symbols(self):
        response = self.get(f'{URL}/symbols')
        assert response.status_code == 200, response.text
        return response.json()

    def candles(self, symbol: str, batch_size: int, candle_size: int) -> List:
        dt = datetime.utcnow()
        seconds = batch_size * candle_size
        params = {
            'from': to_timestamp(dt - timedelta(seconds=seconds)),
            'to': to_timestamp(dt),
            'size': 1,
            'type': 'trades'
        }
        url = f'{URL}/ohlc/{url_encode(symbol)}/{candle_size}'
        pprint(url)
        pprint(params)
        response = self.get(url=url, params=params)
        assert response.status_code == 200, response.text
        candles = response.json()
        for candle in candles:
            candle['datetime'] = from_timestamp(candle['timestamp']).isoformat()
        pprint(candles)
        return candles
