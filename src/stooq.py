import csv
import io
import logging
import shutil
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

from src import tools, session, store, config

LOG = logging.getLogger(__name__)

DT_FORMAT = '%Y%m%d'
URL_ZIP = 'https://static.stooq.com/db/h/{interval}_{country}_txt.zip'
TEMP_PATH = Path('/tmp/stooq/')
COUNTRY_PATH = 'data/{interval}/{country}'
SYMBOL_PATH = '{sub_path}/{symbol}.{country}.txt'

EXCHANGE_COUNTRY = {
    'NYSE': 'us',
    'NASDAQ': 'us',
    'LSE': 'uk',
    'XETRA': 'de',
    'WSE': 'pl'
}

EXCHANGE_PATHS = {
    'NYSE': ('nyse stocks/1', 'nyse stocks/2', 'nyse stocks/3', 'nyse etfs'),
    'NASDAQ': ('nasdaq stocks', 'nasdaq etfs'),
    'LSE': ('lse stocks', 'lse stocks intl'),
    'XETRA': ['xetra'],
    'WSE': ['wse stocks']
}


def stooq_url(interval: timedelta, exchange: str) -> str:
    stooq_interval = {
        tools.INTERVAL_1D: 'd',
        tools.INTERVAL_1W: 'w'
    }[interval]
    return URL_ZIP.format(interval=stooq_interval, country=EXCHANGE_COUNTRY[exchange])


def stooq_country_path(interval: timedelta, exchange: str) -> Path:
    stooq_interval = {
        tools.INTERVAL_1D: 'daily',
        tools.INTERVAL_1W: 'weekly'
    }[interval]
    path = COUNTRY_PATH.format(interval=stooq_interval, country=EXCHANGE_COUNTRY[exchange])
    return TEMP_PATH.joinpath(path)


def stooq_symbol_path(symbol: str, interval: timedelta) -> Optional[Path]:
    short_symbol = '.'.join(symbol.split('.')[:-1]).lower()
    exchange = symbol.split('.')[-1]
    country_path = stooq_country_path(interval, exchange)
    for sub_path in EXCHANGE_PATHS[exchange]:
        path = SYMBOL_PATH.format(sub_path=sub_path,
                                  symbol=short_symbol,
                                  country=EXCHANGE_COUNTRY[exchange])
        symbol_path = country_path.joinpath(path)
        if symbol_path.exists():
            return symbol_path
    return None


def timestamp_from_stooq(date: str):
    dt = datetime.strptime(date, DT_FORMAT)
    return tools.to_timestamp(dt.replace(tzinfo=timezone.utc))


def price_from_stooq(dt: Dict) -> Dict:
    try:
        return {
            'symbol': dt['<TICKER>'],
            'timestamp': timestamp_from_stooq(dt['<DATE>']),
            'open': float(dt['<OPEN>']),
            'close': float(dt['<CLOSE>']),
            'low': float(dt['<LOW>']),
            'high': float(dt['<HIGH>']),
            'volume': int(dt['<VOL>'])
        }
    except:
        return {}


class Session(session.Session):
    def __init__(self, exchanges=None):
        self.interval = tools.INTERVAL_1D
        self.exchanges = exchanges if exchanges else config.ACTIVE_EXCHANGES

        for exchange in self.exchanges:
            path = stooq_country_path(self.interval, exchange)
            if not path.exists():
                url = stooq_url(exchange, self.interval)
                LOG.debug(f'Loading {url} ...')
                response = requests.get(url)
                z = zipfile.ZipFile(io.BytesIO(response.content))
                LOG.debug(f'Extracting {exchange} ...')
                z.extractall(TEMP_PATH)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for exchange in self.exchanges:
            path = stooq_country_path(self.interval, exchange)
            if path.exists():
                shutil.disk_usage(str(path))
                # shutil.rmtree(path)

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Dict]:
        path = stooq_symbol_path(symbol, interval)
        if path is None:
            return []
        with path.open() as read_io:
            result = [price_from_stooq(dt) for dt in csv.DictReader(read_io)]
        return [r for r in result if r]


class Series(store.Series):
    def __init__(self, interval: timedelta, editable=False):
        module = __name__.split('.')[-1]
        name = f'series_{module}_{tools.interval_name(interval)}'
        super().__init__(name, editable)
