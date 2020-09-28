import csv
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from pprint import pprint
from typing import Dict

import requests

from src import tools

DT_FORMAT = '%Y%m%d'
FILES = {'d_us_txt.zip', 'd_uk_txt.zip', 'd_de_txt.zip', 'd_pl_txt.zip'}
URL_ZIP = 'https://static.stooq.com/db/h/d_{name}_txt.zip'
STOCK_PATHS = {'us/nyse stocks',
               'us/nyse etfs',
               'us/nasdaq stocks',
               'us/nasdaq etfs',
               'uk/lse stocks intl',
               'de/xetra',
               'pl/wse stocks'}


def download(name):
    path = '/tmp/stooq/'
    print(f'downloading {name} ...')
    response = requests.get(URL_ZIP.format(name=name))
    z = zipfile.ZipFile(io.BytesIO(response.content))
    print(f'extracting {name} ...')
    z.extractall(path)


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


def load():
    path = Path('/tmp/stooq/data/daily/uk/lse stocks intl/ogzd.uk.txt')
    with path.open() as read_io:
        for dt in csv.DictReader(read_io):
            pprint(price_from_stooq(dt))


if __name__ == '__main__':
    for name in ('us', 'uk', 'de', 'pl'):
        download(name)
    load()
