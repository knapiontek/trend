import csv
import logging
import zipfile
from datetime import datetime, timezone, timedelta
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional

import requests

from src import tool, config, session, store, flow
from src.calendar import Calendar
from src.clazz import Clazz

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
        tool.INTERVAL_1H: 'h',
        tool.INTERVAL_1D: 'd'
    }[interval]
    return ZIP_URL_FORMAT.format(interval=stooq_interval, country=EXCHANGE_COUNTRY[exchange])


def stooq_zip_path(interval: timedelta, exchange: str) -> Path:
    stooq_interval = {
        tool.INTERVAL_1H: 'hourly',
        tool.INTERVAL_1D: 'daily'
    }[interval]
    path = ZIP_PATH_FORMAT.format(interval=stooq_interval, country=EXCHANGE_COUNTRY[exchange])
    return STOOQ_PATH.joinpath(path)


def find_symbol_path(short_symbol: str, interval: timedelta, exchange: str, name_list: List[str]) -> Optional[str]:
    stooq_symbol = short_symbol.replace('.', '-').lower()
    stooq_interval = {
        tool.INTERVAL_1H: 'hourly',
        tool.INTERVAL_1D: 'daily'
    }[interval]
    for path in EXCHANGE_PATHS[exchange]:
        symbol_path = path.format(interval=stooq_interval, symbol=stooq_symbol)
        if symbol_path in name_list:
            return symbol_path
    return None


def timestamp_from_stooq(date: str):
    dt = datetime.strptime(date, DT_FORMAT)
    return Calendar.to_timestamp(dt.replace(tzinfo=timezone.utc))


def datum_from_stooq(dt: Dict, symbol: str) -> Optional[Clazz]:
    try:
        return Clazz(symbol=symbol,
                     timestamp=timestamp_from_stooq(dt['<DATE>']),
                     open=float(dt['<OPEN>']),
                     close=float(dt['<CLOSE>']),
                     low=float(dt['<LOW>']),
                     high=float(dt['<HIGH>']),
                     volume=int(dt['<VOL>']))
    except:
        return None


class Session(session.Session):
    def __init__(self, exchanges=None):
        self.exchanges = exchanges if exchanges else {e: [tool.INTERVAL_1D] for e in config.ACTIVE_EXCHANGES}

        for exchange, intervals in self.exchanges.items():
            for interval in intervals:
                zip_path = stooq_zip_path(interval, exchange)
                zip_path.parent.mkdir(parents=True, exist_ok=True)
                if not tool.is_latest(zip_path, interval, exchange):

                    # start streaming from url
                    url = stooq_url(interval, exchange)
                    response = requests.get(url, stream=True)
                    message = f'Loading {url} to {zip_path.as_posix()}'
                    LOG.info(message)
                    size = int(response.headers["Content-Length"]) // URL_CHUNK_SIZE + 1
                    LOG.debug(f'Size {zip_path.as_posix()}: {size}M')

                    # streaming to the zip file
                    zip_path_pending = zip_path.with_suffix('.pending')
                    with zip_path_pending.open('wb') as zip_io:
                        with flow.Progress(message, size) as progress:
                            for chunk in response.iter_content(URL_CHUNK_SIZE):
                                progress('+')
                                zip_io.write(chunk)
                    zip_path_pending.rename(zip_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for exchange, intervals in self.exchanges.items():
            for interval in intervals:
                zip_path = stooq_zip_path(interval, exchange)
                LOG.debug(f'zip_path: {zip_path.as_posix()} size: {zip_path.stat().st_size / 1024 / 1024:.2f}M')

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Clazz]:
        short_symbol, exchange = tool.symbol_split(symbol)
        ts_from = Calendar.to_timestamp(dt_from)
        ts_to = Calendar.to_timestamp(dt_to)
        zip_path = stooq_zip_path(interval, exchange)
        with zipfile.ZipFile(zip_path) as zip_io:
            relative_path = find_symbol_path(short_symbol, interval, exchange, zip_io.namelist())
            if relative_path:
                content = zip_io.read(relative_path).decode('utf-8')
                data = [datum_from_stooq(dt, symbol) for dt in csv.DictReader(StringIO(content))]
                return [
                    datum
                    for datum in data
                    if datum and ts_from <= datum.timestamp <= ts_to
                ]
        return []


class SecuritySeries(store.SecuritySeries):
    def __init__(self, interval: timedelta, editable=False, dt_from: datetime = None):
        name = f'security_{tool.module_name(__name__)}_{tool.interval_name(interval)}'
        super().__init__(name, editable, dt_from)
