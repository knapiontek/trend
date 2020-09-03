import logging
from datetime import datetime, timedelta
from typing import List, Dict

from yahoofinancials import YahooFinancials

from src import tools, store

LOG = logging.getLogger(__name__)


def symbol_to_yahoo(symbol: str):
    return '-'.join(symbol.split('.')[:-1])


def dt_to_yahoo(dt: datetime):
    return dt.strftime('%Y-%m-%d')


def interval_to_yahoo(interval: timedelta):
    return {
        tools.INTERVAL_1D: 'daily',
        tools.INTERVAL_1W: 'weekly'
    }[interval]


class Session:
    def __enter__(self) -> 'Session':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def series(symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Dict]:
        yahoo_symbol = symbol_to_yahoo(symbol)
        yahoo_from = dt_to_yahoo(dt_from)
        yahoo_to = dt_to_yahoo(dt_to)
        yahoo_interval = interval_to_yahoo(interval)
        items = []

        try:
            yahoo = YahooFinancials(yahoo_symbol)
            prices = yahoo.get_historical_price_data(start_date=yahoo_from,
                                                     end_date=yahoo_to,
                                                     time_interval=yahoo_interval)

            for s, datum in prices.items():
                offset = datum['timeZone']['gmtOffset']
                prices = datum['prices']
                keys = ('date', 'open', 'close', 'low', 'high', 'volume')
                for date, _open, close, low, high, volume in tools.tuple_it(prices, keys):
                    item = {
                        'symbol': symbol,
                        'timestamp': (date + offset) * 1000,
                        'open': _open,
                        'close': close,
                        'low': low,
                        'high': high,
                        'volume': volume
                    }
                    items.append(item)
        except Exception:
            LOG.exception(f'Yahoo Finance problem! Symbol: {symbol}')

        return items


class DBSeries(store.DBSeries):
    def __init__(self, interval: timedelta, editable=False):
        module = __name__.split('.')[-1]
        name = f'series_{module}_{tools.interval_name(interval)}'
        super(DBSeries, self).__init__(name, editable)
