import csv
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import List, Dict

from src import tools, store, session

LOG = logging.getLogger(__name__)

DT_FORMAT = '%Y-%m-%d'
QUOTE_URL = 'https://finance.yahoo.com/quote'
SYMBOL_URL = 'https://query1.finance.yahoo.com/v7/finance/download/{symbol}'
PATTERN = re.compile('"CrumbStore":{"crumb":"(.+?)"}')


def symbol_to_yahoo(symbol: str):
    return '-'.join(symbol.split('.')[:-1])


def dt_to_yahoo(dt: datetime):
    return tools.to_timestamp(dt)


def interval_to_yahoo(interval: timedelta):
    return {
        tools.INTERVAL_1D: '1d',
        tools.INTERVAL_1W: '1wk'
    }[interval]


def timestamp_from_yahoo(date: str):
    dt = datetime.strptime(date, DT_FORMAT)
    return tools.to_timestamp(dt.replace(tzinfo=timezone.utc))


def price_from_yahoo(dt: Dict, symbol: str) -> Dict:
    try:
        return {
            'symbol': symbol,
            'timestamp': timestamp_from_yahoo(dt['Date']),
            'open': float(dt['Open']),
            'close': float(dt['Close']),
            'low': float(dt['Low']),
            'high': float(dt['High']),
            'volume': int(dt['Volume'])
        }
    except:
        return {}


class Session(session.Session):
    def __enter__(self) -> 'Session':
        response = self.get(QUOTE_URL)
        assert response.status_code == 200, response.text
        found = re.search(PATTERN, response.text)
        if not found:
            raise RuntimeError(f'Expected response from the yahoo api: {PATTERN.pattern}')
        self.crumb = found.group(1)
        return self

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Dict]:
        yahoo_symbol = symbol_to_yahoo(symbol)
        yahoo_from = dt_to_yahoo(dt_from)
        yahoo_to = dt_to_yahoo(dt_to + interval)
        yahoo_interval = interval_to_yahoo(interval)

        url = SYMBOL_URL.format(symbol=yahoo_symbol)
        params = {
            'period1': yahoo_from,
            'period2': yahoo_to,
            'interval': yahoo_interval,
            'events': 'history',
            'crumb': self.crumb
        }
        time.sleep(0.6)
        response = self.get(url, params=params)
        if response.status_code == 404:
            return []
        assert response.status_code == 200, f'symbol: {symbol} error: {response.text}'
        data = [price_from_yahoo(item, symbol) for item in csv.DictReader(StringIO(response.text))]
        data = [datum for datum in data if datum]
        if len(data) == 2 and data[0]['timestamp'] == data[1]['timestamp']:
            data = data[0:1]  # if yahoo returns 2 rows with duplicated values
        return data


class Series(store.Series):
    def __init__(self, interval: timedelta, editable=False):
        module = __name__.split('.')[-1]
        name = f'series_{module}_{tools.interval_name(interval)}'
        super().__init__(name, editable)
