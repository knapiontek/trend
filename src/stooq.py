import csv
import logging
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

from src import tools, config, session, store

LOG = logging.getLogger(__name__)

URL_CHUNK_SIZE = 1024 * 1024
STOOQ_PATH = Path('/tmp/stooq/')

DT_FORMAT = '%Y%m%d'
ZIP_URL_FORMAT = 'https://static.stooq.com/db/h/{interval}_{country}_txt.zip'
ZIP_PATH_FORMAT = 'data-{interval}-{country}.zip'

EXCHANGE_COUNTRY = {
    'NYSE': 'us',
    'NASDAQ': 'us',
    'LSE': 'uk',
    'XETRA': 'de',
    'WSE': 'pl'
}

EXCHANGE_PATHS = {
    'NYSE': ('data/{interval}/us/nyse stocks/1/{symbol}.us.txt',
             'data/{interval}/us/nyse stocks/2/{symbol}.us.txt',
             'data/{interval}/us/nyse stocks/3/{symbol}.us.txt'),
    'NASDAQ': ('data/{interval}/us/nasdaq stocks/1/{symbol}.us.txt',
               'data/{interval}/us/nasdaq stocks/2/{symbol}.us.txt'),
    'LSE': ('data/{interval}/uk/lse stocks/{symbol}.uk.txt',
            'data/{interval}/uk/lse stocks intl/{symbol}.uk.txt'),
    'XETRA': ['data/{interval}/de/xetra stocks/{symbol}.de.txt'],
    'WSE': ['data/{interval}/pl/wse stocks/{symbol}.txt']
}


def stooq_url(interval: timedelta, exchange: str) -> str:
    stooq_interval = {
        tools.INTERVAL_1H: 'h',
        tools.INTERVAL_1D: 'd'
    }[interval]
    return ZIP_URL_FORMAT.format(interval=stooq_interval, country=EXCHANGE_COUNTRY[exchange])


def stooq_zip_path(interval: timedelta, exchange: str) -> Path:
    stooq_interval = {
        tools.INTERVAL_1H: 'hourly',
        tools.INTERVAL_1D: 'daily'
    }[interval]
    path = ZIP_PATH_FORMAT.format(interval=stooq_interval, country=EXCHANGE_COUNTRY[exchange])
    return STOOQ_PATH.joinpath(path)


def stooq_symbol_path(short_symbol: str, exchange: str, interval: timedelta, name_list: List[str]) -> Optional[str]:
    stooq_interval = {
        tools.INTERVAL_1H: 'hourly',
        tools.INTERVAL_1D: 'daily'
    }[interval]
    for path in EXCHANGE_PATHS[exchange]:
        symbol_path = path.format(interval=stooq_interval, symbol=short_symbol.replace('.', '-').lower())
        if symbol_path in name_list:
            return symbol_path
    return None


def timestamp_from_stooq(date: str):
    dt = datetime.strptime(date, DT_FORMAT)
    return tools.to_timestamp(dt.replace(tzinfo=timezone.utc))


def price_from_stooq(dt: Dict, symbol: str) -> Dict:
    try:
        return {
            'symbol': symbol,
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
        self.exchanges = exchanges if exchanges else {e: [tools.INTERVAL_1D] for e in config.ACTIVE_EXCHANGES}

        for exchange, intervals in self.exchanges.items():
            for interval in intervals:
                zip_path = stooq_zip_path(interval, exchange)
                zip_path.parent.mkdir(parents=True, exist_ok=True)
                if not tools.is_latest(zip_path, exchange, interval):
                    url = stooq_url(interval, exchange)
                    response = requests.get(url, stream=True)
                    message = f'Loading {url} to {zip_path.as_posix()}'
                    LOG.info(message)
                    size = int(response.headers["Content-Length"]) // URL_CHUNK_SIZE + 1
                    LOG.debug(f'Size {zip_path.as_posix()}: {size}M')
                    with zip_path.open('wb') as zip_io:
                        with tools.Progress(message, size) as progress:
                            for chunk in response.iter_content(URL_CHUNK_SIZE):
                                progress('+')
                                zip_io.write(chunk)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for exchange, intervals in self.exchanges.items():
            for interval in intervals:
                zip_path = stooq_zip_path(interval, exchange)
                LOG.debug(f'zip_path: {zip_path.as_posix()} size: {zip_path.stat().st_size / 1024 / 1024:.2f}M')

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Dict]:
        short_symbol, exchange = tools.symbol_split(symbol)
        zip_path = stooq_zip_path(interval, exchange)
        with zipfile.ZipFile(zip_path) as zip_io:
            name_list = zip_io.namelist()
            path = stooq_symbol_path(short_symbol, exchange, interval, name_list)
            if path is None:
                return []
            zip_io.extract(path, STOOQ_PATH)

        with STOOQ_PATH.joinpath(path).open() as read_io:
            prices = [price_from_stooq(dt, symbol) for dt in csv.DictReader(read_io)]
        return [
            price
            for price in prices
            if price and tools.to_timestamp(dt_from) <= price['timestamp'] <= tools.to_timestamp(dt_to)
        ]


class Series(store.Series):
    def __init__(self, interval: timedelta, editable=False):
        name = f'series_{tools.module_name(__name__)}_{tools.interval_name(interval)}'
        super().__init__(name, editable)
