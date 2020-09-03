import csv
import json
import re
import time
from datetime import datetime
from io import StringIO
from typing import Dict

import requests

DT_FORMAT = '%Y-%m-%d'


def timestamp_from_yahoo(date: str):
    dt = datetime.strptime(date, DT_FORMAT)
    return int(time.mktime(dt.utctimetuple()))


SYMBOLS = ['XOM', 'AAPL']
PERIOD1 = timestamp_from_yahoo('2020-08-12')
PERIOD2 = timestamp_from_yahoo('2020-08-22')
INTERVAL = '1d'

QUOTE_URL = 'https://finance.yahoo.com/quote'
SYMBOL_URL = 'https://query1.finance.yahoo.com/v7/finance/download/{symbol}'
PATTERN = re.compile('"CrumbStore":{"crumb":"(.+?)"}')


def from_yahoo(dt: Dict) -> Dict:
    return {
        'timestamp': timestamp_from_yahoo(dt['Date']),
        'open': float(dt['Open']),
        'close': float(dt['Close']),
        'low': float(dt['Low']),
        'high': float(dt['High']),
        'volume': int(dt['Volume'])
    }


with requests.Session() as session:
    response = session.get(QUOTE_URL)
    assert response.status_code == 200, response.text
    found = re.search(PATTERN, response.text)
    if found:
        crumb = found.group(1)
        for symbol in SYMBOLS:
            url = SYMBOL_URL.format(symbol=symbol)
            params = {
                'period1': PERIOD1,
                'period2': PERIOD2,
                'interval': INTERVAL,
                'events': 'history',
                'crumb': crumb
            }
            response = session.get(url, params=params)
            data = [from_yahoo(item) for item in csv.DictReader(StringIO(response.text))]
            print(json.dumps(data, indent=2))
    else:
        print('Problem')
