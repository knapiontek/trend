import csv
import logging
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

from src import tools, session, store, config

LOG = logging.getLogger(__name__)

DT_FORMAT = '%Y%m%d'
URL_CHUNK_SIZE = 1024 * 1024
ZIP_URL = 'https://static.stooq.com/db/h/{interval}_{country}_txt.zip'
STOOQ_PATH = Path('/tmp/stooq/')
COUNTRY_PATH = 'data/{interval}/{country}'

EXCHANGE_COUNTRY = {
    'NYSE': 'us',
    'NASDAQ': 'us',
    'LSE': 'uk',
    'XETRA': 'de',
    'WSE': 'pl'
}

EXCHANGE_PATHS = {
    'NYSE': ('nyse stocks/1/{symbol}.us.txt',
             'nyse stocks/2/{symbol}.us.txt',
             'nyse stocks/3/{symbol}.us.txt'),
    'NASDAQ': ('nasdaq stocks/1/{symbol}.us.txt', 'nasdaq stocks/2/{symbol}.us.txt'),
    'LSE': ('lse stocks/{symbol}.uk.txt', 'lse stocks intl/{symbol}.uk.txt'),
    'XETRA': ['xetra stocks/{symbol}.de.txt'],
    'WSE': ['wse stocks/{symbol}.txt']
}


def stooq_url(interval: timedelta, exchange: str) -> str:
    stooq_interval = {
        tools.INTERVAL_1H: 'h',
        tools.INTERVAL_1D: 'd'
    }[interval]
    return ZIP_URL.format(interval=stooq_interval, country=EXCHANGE_COUNTRY[exchange])


def stooq_country_path(interval: timedelta, exchange: str) -> Path:
    stooq_interval = {
        tools.INTERVAL_1H: 'hourly',
        tools.INTERVAL_1D: 'daily'
    }[interval]
    path = COUNTRY_PATH.format(interval=stooq_interval, country=EXCHANGE_COUNTRY[exchange])
    return STOOQ_PATH.joinpath(path)


def stooq_symbol_path(symbol: str, interval: timedelta) -> Optional[Path]:
    short_symbol, exchange = tools.symbol_split(symbol)
    country_path = stooq_country_path(interval, exchange)
    for path in EXCHANGE_PATHS[exchange]:
        symbol_path = country_path.joinpath(path.format(symbol=short_symbol.lower()))
        if symbol_path.exists():
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
                path = stooq_country_path(interval, exchange)
                if not tools.is_latest(path, exchange, interval):
                    url = stooq_url(interval, exchange)
                    zip_path = STOOQ_PATH.joinpath(f'{EXCHANGE_COUNTRY[exchange]}.zip')
                    zip_path.parent.mkdir(parents=True, exist_ok=True)

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

                    message = f'Extracting {zip_path.as_posix()}'
                    LOG.info(message)
                    with zipfile.ZipFile(zip_path) as zip_io:
                        name_list = zip_io.namelist()
                        with tools.Progress(message, name_list) as progress:
                            for name in name_list:
                                progress(name)
                                zip_io.extract(name, STOOQ_PATH)

                    zip_path.unlink()
                    path.touch()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for exchange, intervals in self.exchanges.items():
            for interval in intervals:
                path = stooq_country_path(interval, exchange)
                if path.exists():
                    size = sum(file.stat().st_size for file in path.rglob('*'))
                    LOG.debug(f'path: {path.as_posix()} size: {size / 1024 / 1024:.2f}M')

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Dict]:
        path = stooq_symbol_path(symbol, interval)
        if path is None:
            return []
        with path.open() as read_io:
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
