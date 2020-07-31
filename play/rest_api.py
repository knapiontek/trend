import json
import operator
import time
from datetime import timezone, timedelta, datetime
from pprint import pprint
from typing import Dict, Optional

import requests

AUTH = ('?', '?')
URL = 'https://api-demo.exante.eu/md/2.0'
URL_EXCHANGES = f'{URL}/exchanges'
URL_ACCOUNTS = f'{URL}/accounts'
URL_ACCOUNT_SUMMARY = f'{URL}/summary'
URL_STOCK = f'{URL}/types/STOCK'
URL_FEED = f'{URL}/feed/XOM.NYSE,KRU.WSE'
URL_FEED_LAST = f'{URL}/feed/XOM.NYSE,KRU.WSE/last'
STREAM_HEADER = {'accept': 'application/x-json-stream'}
STOCK_FILE = 'stock.json'


def run_session():
    with requests.Session() as session:
        session.auth = AUTH

        response = session.get(url=URL_ACCOUNTS)
        assert response.status_code == 200, response.text

        accounts = response.json()
        for account in accounts:
            account_id = account['accountId']
            url_summary = f'{URL_ACCOUNT_SUMMARY}/{account_id}/EUR'
            pprint(url_summary)
            response = session.get(url=url_summary)
            assert response.status_code == 200, response.text
            pprint(response.json())

            pprint(URL_FEED_LAST)
            response = session.get(url=URL_FEED_LAST)
            assert response.status_code == 200, response.text
            pprint(response.json())

            pprint(URL_FEED)
            response = session.get(url=URL_FEED, stream=True, headers=STREAM_HEADER)
            assert response.status_code == 200, response.text
            for line in response.iter_lines():
                pprint(json.loads(line))


def store_stock():
    with requests.Session() as session:
        session.auth = AUTH

        response = session.get(url=URL_STOCK)
        assert response.status_code == 200, response.text

        stock = response.json()
        stock = [s for s in stock if s['exchange'] in {'NYSE'}]

        pprint(f'Stock size: {len(stock)}')

        with open(STOCK_FILE, 'w') as stock_io:
            json.dump(stock, stock_io, indent=2)


def query_stock():
    with open(STOCK_FILE) as stock_io:
        stock = json.load(stock_io)

    stock = [s['id'] for s in stock if '/' not in s['id']]

    with requests.Session() as session:
        session.auth = AUTH

        for chunk in [stock[i:i + 5] for i in range(0, len(stock), 5)]:
            stock_list = ','.join(chunk[:5])

            url = f'{URL}/feed/{stock_list}/last'
            pprint(url)
            response = session.get(url=url, data={'level': 'best_price'})
            assert response.status_code == 200, response.text
            pprint(response.json())


DUBLIN_TZ = timezone(timedelta(hours=1), 'GMT')


def to_timestamp(dt: datetime) -> int:
    return int(time.mktime(dt.utctimetuple()) * 1000 + dt.microsecond / 1000)


def from_timestamp(ts: int) -> datetime:
    return datetime.fromtimestamp(ts / 1000, tz=DUBLIN_TZ)


def query_stock_by_time(session: requests.Session, symbol, dt: datetime) -> Optional[Dict]:
    url = f'{URL}/ohlc/{symbol}/60'
    pprint(url)
    data = {
        'from': to_timestamp(dt - timedelta(minutes=1)),
        'to': to_timestamp(dt),
        'size': 1,
        'type': 'trades'
    }
    response = session.get(url=url, params=data)
    if response.status_code == 200:
        candles = response.json()
        for candle in candles:
            candle['datetime'] = from_timestamp(candle['timestamp']).isoformat()
        return candles[-1] if candles else None
    return None


def find_gaps():
    dt_close = datetime(2020, 7, 10, 21, 0, 0, tzinfo=DUBLIN_TZ)
    dt_open = datetime(2020, 7, 13, 14, 31, 0, tzinfo=DUBLIN_TZ)
    pprint(f'datetime: {dt_open.isoformat()}')

    with requests.Session() as session:
        session.auth = AUTH

        url_nyse = f'{URL_EXCHANGES}/NYSE'
        response = session.get(url=url_nyse)
        assert response.status_code == 200, response.text
        stock = [s['id'] for s in response.json() if '/' not in s['id']]

        gaps = {}
        for symbol in stock:
            result_close = query_stock_by_time(session, symbol, dt_close)
            if result_close:
                result_open = query_stock_by_time(session, symbol, dt_open)
                if result_open:
                    price_close = float(result_close['close'])
                    price_open = float(result_open['open'])
                    gap = abs(price_open - price_close) / price_close
                    gaps[symbol] = gap
                    print(f'{symbol}: {gap}')
        print('RESULTS')
        pprint(sorted(gaps.items(), key=operator.itemgetter(1), reverse=True))


if __name__ == '__main__':
    # run_session()
    # store_stock()
    start = time.time()
    find_gaps()
    end = time.time()
    elapsed = end - start
    pprint(time.strftime("%H:%M:%S", time.gmtime(elapsed)))
