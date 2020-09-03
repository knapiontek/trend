import csv
import logging
import re
import time
from datetime import datetime, timedelta
from io import StringIO
from typing import List, Dict

import requests

from src import tools, store

LOG = logging.getLogger(__name__)

DT_FORMAT = '%Y-%m-%d'
QUOTE_URL = 'https://finance.yahoo.com/quote'
SYMBOL_URL = 'https://query1.finance.yahoo.com/v7/finance/download/{symbol}'
PATTERN = re.compile('"CrumbStore":{"crumb":"(.+?)"}')


def symbol_to_yahoo(symbol: str):
    return '-'.join(symbol.split('.')[:-1])


def dt_to_yahoo(dt: datetime):
    return int(time.mktime(dt.utctimetuple()))


def interval_to_yahoo(interval: timedelta):
    return {
        tools.INTERVAL_1D: '1d',
        tools.INTERVAL_1W: '1wk'
    }[interval]


def timestamp_from_yahoo(date: str):
    dt = datetime.strptime(date, DT_FORMAT)
    return tools.to_ts_ms(dt)


def price_from_yahoo(dt: Dict, symbol: str) -> Dict:
    return {
        'symbol': symbol,
        'timestamp': timestamp_from_yahoo(dt['Date']),
        'open': float(dt['Open']),
        'close': float(dt['Close']),
        'low': float(dt['Low']),
        'high': float(dt['High']),
        'volume': int(dt['Volume'])
    }


class Session(requests.Session):
    def __enter__(self) -> 'Session':
        response = self.get(QUOTE_URL)
        assert response.status_code == 200, response.text
        found = re.search(PATTERN, response.text)
        if not found:
            raise RuntimeError('Yahoo API')
        self.crumb = found.group(1)
        return self

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Dict]:
        yahoo_symbol = symbol_to_yahoo(symbol)
        yahoo_from = dt_to_yahoo(dt_from)
        yahoo_to = dt_to_yahoo(dt_to)
        yahoo_interval = interval_to_yahoo(interval)

        url = SYMBOL_URL.format(symbol=yahoo_symbol)
        params = {
            'period1': yahoo_from,
            'period2': yahoo_to,
            'interval': yahoo_interval,
            'events': 'history',
            'crumb': self.crumb
        }
        response = self.get(url, params=params)
        assert response.status_code == 200, response.text
        return [price_from_yahoo(item, symbol) for item in csv.DictReader(StringIO(response.text))]


class DBSeries(store.DBSeries):
    def __init__(self, interval: timedelta, editable=False):
        module = __name__.split('.')[-1]
        name = f'series_{module}_{tools.interval_name(interval)}'
        super(DBSeries, self).__init__(name, editable)
