import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict

from src import store, log, tools, holidays, exante

LOG = logging.getLogger(__name__)


def read_sp500() -> Dict:
    import pandas as pd
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    df = table[0]
    df = df.where(pd.notnull(df), None)
    dt = df.to_dict('split')
    return {
        'schema': dt['columns'],
        'data': dt['data']
    }


def reload_exchanges():
    sp500 = read_sp500()
    sp500_symbols = [symbol for symbol, security in tools.tuple_it(sp500, ['Symbol', 'Security'])]
    with store.FileStore('exchanges', editable=True) as content:
        with exante.Session() as session:
            for exchange in ['NYSE', 'NASDAQ']:
                symbols = session.symbols(exchange)
                content[exchange] = [s for s in symbols if s['ticker'] in sp500_symbols]
                LOG.info(f'imported {len(content[exchange])} instruments from {exchange}')


def show_instrument_range():
    with store.DBSeries(tools.INTERVAL_1D) as series:
        time_range = series.time_range()
        print(json.dumps(time_range))


def update_series():
    with store.FileStore('exchanges') as exchanges:
        instruments = sum([v for k, v in exchanges.items()], [])
    LOG.debug(f'loaded instruments: {len(instruments)}')
    symbols = [i['symbolId'] for i in instruments]

    interval = tools.INTERVAL_1D
    delta = interval * 1000
    dt_from_default = datetime(2017, 12, 31)
    dt_to = tools.dt_round(datetime.utcnow(), interval)

    with store.DBSeries(interval) as db_series:
        time_range = db_series.time_range()
    LOG.debug(f'loaded time-range entries: {len(time_range)}')

    latest = {r['symbol']: tools.from_ts_ms(r['max_ts']) for r in time_range}
    instruments_latest = {s: latest.get(s) or dt_from_default for s in symbols}

    with exante.Session() as session:
        for symbol, dt_from in instruments_latest.items():
            for slice_from, slice_to in tools.time_slices(dt_from, dt_to, delta, interval):
                time_series = session.series(symbol, slice_from, slice_to, interval)

                with store.DBSeries(interval, editable=True) as db_series:
                    db_series += time_series


def verify_instrument(symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> Dict[str, List]:
    health = {}
    with store.DBSeries(interval) as db_series:
        series = db_series[symbol]

    exchange = symbol.split('.')[-1]
    db_dates = {tools.from_ts_ms(s['timestamp']) for s in series}
    overlap = db_dates & holidays.HOLIDAYS[exchange]
    if overlap:
        health['overlap'] = list(overlap)
    all_days = db_dates | holidays.HOLIDAYS[exchange]

    missing = []
    start = dt_from
    while start < dt_to:
        if start.weekday() in (0, 1, 2, 3, 4):
            date = tools.dt_format(start)
            if date not in all_days:
                missing.append(date)
        start += interval
    if missing:
        health['missing'] = missing

    return health


def verify_series():
    interval = tools.INTERVAL_1D
    with store.DBSeries(interval) as series:
        time_range = series.time_range()
    length = len(time_range)
    LOG.debug(f'loaded time-range entries: {length}')

    progress = tools.Progress('series-health', length)
    with store.FileStore('series-health', editable=True) as health:
        for symbol, ts_from, ts_to in tools.tuple_it(time_range, ('symbol', 'min_ts', 'max_ts')):
            symbol_health = verify_instrument(symbol, tools.from_ts_ms(ts_from), tools.from_ts_ms(ts_to), interval)
            if symbol_health:
                health[symbol] = symbol_health
            progress += 1


if __name__ == '__main__':
    log.init(__file__, persist=False)

    # reload_exchanges()
    update_series()
    # verify_series()
