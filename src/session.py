import logging
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import List

import requests

from src import config

LOG = logging.getLogger(__name__)

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
            'from': to_timestamp(dt_from),
            'to': to_timestamp(dt_to),
            'size': 1000,
            'type': 'trades'
        }
        url = f'{URL}/ohlc/{url_encode(symbol)}/{duration}'
        LOG.debug(f'url: {url} from: {dt_from} to: {dt_to}')
        response = self.get(url=url, params=params)
        assert response.status_code == 200, response.text
        candles = response.json()
        for candle in candles:
            candle['datetime'] = from_timestamp(candle['timestamp']).isoformat()
        LOG.debug(f'received candles: {len(candles)} last: {candles[-1]["datetime"]}')
        return candles
