import logging
from datetime import datetime, timedelta
from typing import List

import requests

from src import config, tools

LOG = logging.getLogger(__name__)

URL = config.exante_url()

DURATION_1M = 60
DURATION_5M = 5 * 60
DURATION_10M = 10 * 60
DURATION_15M = 15 * 60
DURATION_1H = 60 * 60
DURATION_6H = 6 * 60 * 60
DURATION_1D = 24 * 60 * 60


def dt_round(dt: datetime, duration: int) -> datetime:
    return {
        DURATION_1M: lambda: dt.replace(minute=0, second=0, microsecond=0),
        DURATION_5M: lambda: dt.replace(minute=0, second=0, microsecond=0),
        DURATION_10M: lambda: dt.replace(minute=0, second=0, microsecond=0),
        DURATION_15M: lambda: dt.replace(minute=0, second=0, microsecond=0),
        DURATION_1H: lambda: dt.replace(minute=0, second=0, microsecond=0),
        DURATION_6H: lambda: dt.replace(hour=dt.hour % 6, minute=0, second=0, microsecond=0),
        DURATION_1D: lambda: dt.replace(hour=0, minute=0, second=0, microsecond=0)
    }[duration]()


def interval_to_duration(interval: timedelta):
    return {
        tools.INTERVAL_1H: DURATION_1H,
        tools.INTERVAL_1D: DURATION_1D
    }[interval]


class Session(requests.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.auth = config.exante_auth()

    def symbols(self, exchange: str):
        response = self.get(f'{URL}/exchanges/{exchange}')
        assert response.status_code == 200, response.text
        return response.json()

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List:
        max_size = 1000
        symbol_dict = {'symbol': symbol}
        params = {
            'from': tools.to_ts_ms(dt_from),
            'to': tools.to_ts_ms(dt_to),
            'size': max_size,
            'type': 'trades'
        }
        duration = interval_to_duration(interval)
        url = f'{URL}/ohlc/{tools.url_encode(symbol)}/{duration}'
        LOG.debug(f'url: {url} from: {tools.dt_format(dt_from)} to: {tools.dt_format(dt_to)}')
        response = self.get(url=url, params=params)
        assert response.status_code == 200, response.text
        candles = response.json()
        size = len(candles)
        assert size < max_size
        LOG.debug(f'received candles: {size}')
        return [{**c, **symbol_dict} for c in candles]  # add symbol
