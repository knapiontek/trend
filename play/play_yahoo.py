import csv
import json
import re
import time
from datetime import datetime
from io import StringIO

import requests

DT_FORMAT = '%Y-%m-%d'


def timestamp_parse(date: str):
    dt = datetime.strptime(date, DT_FORMAT)
    return int(time.mktime(dt.utctimetuple()))


SYMBOL = 'XOM'
PERIOD1 = timestamp_parse('2020-08-12')
PERIOD2 = timestamp_parse('2020-08-22')
INTERVAL = '1d'

LOGIN_URL = f'https://finance.yahoo.com/quote/{SYMBOL}/?p={SYMBOL}'
PATTERN = re.compile('"CrumbStore":{"crumb":"(.+?)"}')

KEYS = {
    'Date': 'date',
    'Open': 'open',
    'Close': 'close',
    'Low': 'log',
    'High': 'high',
    'Volume': 'volume'
}

with requests.Session() as session:
    response = session.get(LOGIN_URL)
    assert response.status_code == 200, response.text
    found = re.search(PATTERN, response.text)
    if found:
        crumb = found.group(1)
        url = f'https://query1.finance.yahoo.com/v7/finance/download/{SYMBOL}'
        params = {
            'period1': PERIOD1,
            'period2': PERIOD2,
            'interval': INTERVAL,
            'events': 'history',
            'crumb': crumb
        }
        response = session.get(url, params=params)
        data = [{v: item[k] for k, v in KEYS.items()} for item in csv.DictReader(StringIO(response.text))]
        print(json.dumps(data, indent=2))
    else:
        print('Problem')
