import logging
from datetime import timedelta
from typing import List, Dict, Optional

import requests

from src import config, tool, store, session
from src.clazz import Clazz
from src.tool import DateTime

LOG = logging.getLogger(__name__)

DATA_URL = 'https://api-live.exante.eu/md/3.0'
TRADE_URL = 'https://api-live.exante.eu/trade/3.0'


def datetime_to_exante(dt: DateTime) -> int:
    return dt.to_timestamp() * 1000


def timestamp_from_exante(timestamp: int):
    return timestamp // 1000


def interval_to_exante(interval: timedelta):
    return {
        tool.INTERVAL_1H: 60 * 60,
        tool.INTERVAL_1D: 24 * 60 * 60
    }[interval]


def datum_from_exante(dt: Dict, symbol: str) -> Optional[Clazz]:
    try:
        return Clazz(symbol=symbol,
                     timestamp=timestamp_from_exante(dt['timestamp']),
                     open=float(dt['open']),
                     close=float(dt['close']),
                     low=float(dt['low']),
                     high=float(dt['high']),
                     volume=int(dt['volume']))
    except:
        return None


class Session(session.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.auth = config.exante_auth()

    def securities(self, exchange: str) -> List[Clazz]:
        url = f'{DATA_URL}/exchanges/{exchange}'
        response = self.get(url)
        assert response.status_code == 200, f'url: {url} reply: {response.text}'
        keys = dict(symbol='symbolId',
                    type='symbolType',
                    exchange='exchange',
                    currency='currency',
                    name='name',
                    description='description',
                    short_symbol='ticker')
        return [Clazz({k: item[v] for k, v in keys.items()}) for item in response.json()]

    def series(self, symbol: str, dt_from: DateTime, dt_to: DateTime, interval: timedelta) -> List[Clazz]:
        exante_from = datetime_to_exante(dt_from)
        exante_to = datetime_to_exante(dt_to)
        exante_interval = interval_to_exante(interval)

        url = f'{DATA_URL}/ohlc/{tool.url_encode(symbol)}/{exante_interval}'
        max_size = 4096
        params = {'from': exante_from, 'to': exante_to, 'size': max_size, 'type': 'trades'}
        response = self.get(url, params=params)
        if response.status_code == 404:
            return []
        assert response.status_code == 200, f'url: {url} params: {params} reply: {response.text}'
        data = [datum_from_exante(datum, symbol) for datum in response.json()]
        assert len(data) < max_size
        return list(filter(None, data))

    def transactions(self) -> List[dict]:
        url = f'{DATA_URL}/transactions'
        response = self.get(url)
        return response.json()

    def orders(self) -> List[dict]:
        url = f'{TRADE_URL}/orders'
        response = self.get(url)
        return response.json()

    def place_order(self, symbol: str, limit: float, stop_loss: float):
        params = {'side': 'buy',
                  'duration': 'day',
                  'quantity': '1',
                  'symbolId': symbol,
                  'ocoGroup': None,
                  'ifDoneParentId': None,
                  'orderType': 'limit',
                  'limitPrice': str(limit),
                  'stopLoss': str(stop_loss)}
        url = f'{TRADE_URL}/orders'
        response = self.post(url, params=params)
        return response.json()


class SecuritySeries(store.SecuritySeries):
    def __init__(self, interval: timedelta, editable=False, dt_from: DateTime = None):
        name = f'security_{tool.source_name(__name__, interval)}'
        super().__init__(name, editable, dt_from)


def read_shortables() -> Dict[str, bool]:
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
    read_shortables()
