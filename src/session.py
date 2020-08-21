import logging
from datetime import datetime, timedelta
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

    def candles(self, symbol: str, batch_size: int, duration: int) -> List:
        seconds = batch_size * duration
        dt_to = datetime.now(tz=config.UTC_TZ)
        dt_from = dt_to - timedelta(seconds=seconds)
        params = {
            'from': tools.to_ts_ms(dt_from),
            'to': tools.to_ts_ms(dt_to),
            'size': 1000,
            'type': 'trades'
        }
        url = f'{URL}/ohlc/{tools.url_encode(symbol)}/{duration}'
        LOG.debug(f'url: {url} from: {tools.dt_format(dt_from)} to: {tools.dt_format(dt_to)}')
        response = self.get(url=url, params=params)
        assert response.status_code == 200, response.text
        candles = response.json()
        for candle in candles:
            timestamp = candle['timestamp']
            candle['utc'] = tools.dt_format(tools.from_ts_ms(timestamp, config.UTC_TZ))
            candle['dublin'] = tools.dt_format(tools.from_ts_ms(timestamp, config.DUBLIN_TZ))
        LOG.debug(f'received candles: {len(candles)} last: {candles[-1]["utc"]}')
        return candles
