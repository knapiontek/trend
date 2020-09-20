import csv
import io
import zipfile
from pathlib import Path
from pprint import pprint

import requests


def download():
    zip_file_url = 'https://static.stooq.com/db/h/d_uk_txt.zip'
    path = '/tmp/d_uk_txt'
    print('downloading ...')
    response = requests.get(zip_file_url)
    z = zipfile.ZipFile(io.BytesIO(response.content))
    print('extracting ...')
    z.extractall(path)


def load():
    keys = {
        '<TICKER>': 'symbol',
        '<DATE>': 'timestamp',
        '<OPEN>': 'open',
        '<HIGH>': 'high',
        '<LOW>': 'low',
        '<CLOSE>': 'close',
        '<VOL>': 'volume'
    }
    path = Path('/tmp/d_uk_txt/data/daily/uk/lse stocks intl/ogzd.uk.txt')
    with path.open() as read_io:
        for item in csv.DictReader(read_io):
            pprint({v: item[k] for k, v in keys.items()})


if __name__ == '__main__':
    load()
