import logging
from datetime import datetime
from typing import List

import requests

from src import config, tools

LOG = logging.getLogger(__name__)

URL = config.exante_url()


class ExanteSession(requests.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.auth = config.exante_auth()

    def symbols(self, exchange: str):
        response = self.get(f'{URL}/exchanges/{exchange}')
        assert response.status_code == 200, response.text
        return response.json()

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, duration: int) -> List:
        max_size = 1000
        symbol_dict = {'symbol': symbol}
        params = {
            'from': tools.to_ts_ms(dt_from),
            'to': tools.to_ts_ms(dt_to),
            'size': max_size,
            'type': 'trades'
        }
        url = f'{URL}/ohlc/{tools.url_encode(symbol)}/{duration}'
        LOG.debug(f'url: {url} from: {tools.dt_format(dt_from)} to: {tools.dt_format(dt_to)}')
        response = self.get(url=url, params=params)
        assert response.status_code == 200, response.text
        candles = response.json()
        size = len(candles)
        assert size < max_size
        LOG.debug(f'received candles: {size}')
        for candle in candles:
            timestamp = candle['timestamp']
            candle['utc'] = tools.ts_format(timestamp, tools.UTC_TZ)
            candle['dublin'] = tools.ts_format(timestamp, tools.DUBLIN_TZ)
        return [{**c, **symbol_dict} for c in candles]  # add symbol
