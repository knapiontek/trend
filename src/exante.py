import logging
from datetime import datetime, timedelta
from typing import List, Dict

import requests

from src import config, tools, store, session

LOG = logging.getLogger(__name__)

DATA_URL = 'https://api-live.exante.eu/md/3.0'
TRADE_URL = 'https://api-live.exante.eu/trade/3.0'


def dt_to_exante(dt: datetime):
    return tools.to_timestamp(dt) * 1000


def interval_to_exante(interval: timedelta):
    return {
        tools.INTERVAL_1H: 60 * 60,
        tools.INTERVAL_1D: 24 * 60 * 60
    }[interval]


def timestamp_from_exante(ts: int):
    return ts // 1000


def price_from_exante(dt: Dict, symbol: str) -> Dict:
    try:
        return {
            'symbol': symbol,
            'timestamp': timestamp_from_exante(dt['timestamp']),
            'open': float(dt['open']),
            'close': float(dt['close']),
            'low': float(dt['low']),
            'high': float(dt['high']),
            'volume': int(dt['volume'])
        }
    except:
        return {}


class Session(session.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.auth = config.exante_auth()

    def symbols(self, exchange: str):
        response = self.get(f'{DATA_URL}/exchanges/{exchange}')
        assert response.status_code == 200, response.text
        return response.json()

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Dict]:
        exante_from = dt_to_exante(dt_from)
        exante_to = dt_to_exante(dt_to)
        exante_interval = interval_to_exante(interval)

        url = f'{DATA_URL}/ohlc/{tools.url_encode(symbol)}/{exante_interval}'
        max_size = 1000
        params = {
            'from': exante_from,
            'to': exante_to,
            'size': max_size,
            'type': 'trades'
        }
        response = self.get(url, params=params)
        assert response.status_code == 200, response.text
        data = response.json()
        size = len(data)
        assert size < max_size
        return [price_from_exante(datum, symbol) for datum in data]


class DBSeries(store.DBSeries):
    def __init__(self, interval: timedelta, editable=False):
        module = __name__.split('.')[-1]
        name = f'series_{module}_{tools.interval_name(interval)}'
        super().__init__(name, editable)


def read_short_allowance() -> Dict[str, bool]:
    import re
    import xlrd
    xls = config.EXANTE_PATH.joinpath('short-allowance.xls')
    workbook = xlrd.open_workbook(xls)
    sheet = workbook.sheet_by_name('main')
    boolean = {'Yes': True, 'No': False}
    pattern = re.compile('(.+?) / (.+?) / (.+)')
    return {
        re.sub(pattern, '\\3.\\2', sheet.cell(i, 0).value): boolean[sheet.cell(i, 1).value]
        for i in range(1, sheet.nrows)
    }


if __name__ == '__main__':
    read_short_allowance()
