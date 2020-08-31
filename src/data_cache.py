import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict

from src import store, session, log, tools, holidays

LOG = logging.getLogger(__name__)


def show_instrument_range():
    with store.DBSeries(tools.DURATION_1D) as series:
        time_range = series.time_range()
        print(json.dumps(time_range))


def update_series():
    log.init(__file__, persist=False)

    with store.FileStore('exchanges') as exchanges:
        instruments = sum([v for k, v in exchanges.items()], [])
    LOG.debug(f'loaded instruments: {len(instruments)}')
    symbols = [i['symbolId'] for i in instruments][:10]

    duration = tools.DURATION_1D
    slice_delta = timedelta(seconds=1000 * duration)
    time_delta = timedelta(seconds=duration)
    dt_from_default = datetime(2017, 12, 31, tzinfo=tools.UTC_TZ)
    dt_to = tools.dt_truncate(datetime.now(tz=tools.UTC_TZ), duration)

    with store.DBSeries(duration) as series:
        time_range = series.time_range()
    LOG.debug(f'loaded time-range entries: {len(time_range)}')

    latest = {r['symbol']: tools.dt_parse(r['max_utc']) for r in time_range}
    instruments_latest = {s: latest.get(s) or dt_from_default for s in symbols}

    with session.ExanteSession() as exante:
        for symbol, dt_from in instruments_latest.items():
            for slice_from, slice_to in tools.time_slices(dt_from, dt_to, slice_delta, time_delta):
                time_series = exante.series(symbol, slice_from, slice_to, duration)

                with store.DBSeries(duration, editable=True) as db_series:
                    db_series += time_series


def verify_instrument(symbol: str, dt_from: datetime, dt_to: datetime, duration: int) -> Dict[str, List]:
    health = {}
    time_delta = timedelta(seconds=duration)
    with store.DBSeries(duration) as db_series:
        series = db_series[symbol]

    db_dates = {daily['utc'] for daily in series}
    exchange = symbol.split('.')[-1]
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
        start += time_delta
    if missing:
        health['missing'] = missing

    return health


def verify_series():
    log.init(__file__, persist=False)

    duration = tools.DURATION_1D
    with store.DBSeries(duration) as series:
        time_range = series.time_range()
    length = len(time_range)
    LOG.debug(f'loaded time-range entries: {length}')

    with store.FileStore('series-health', editable=True) as health:
        for i, (symbol, dt_from, dt_to) in enumerate(tools.stream(time_range, ('symbol', 'min_utc', 'max_utc'))):
            symbol_health = verify_instrument(symbol, tools.dt_parse(dt_from), tools.dt_parse(dt_to), duration)
            if symbol_health:
                health[symbol] = symbol_health
            tools.progress(i, length)


def reload_exchanges():
    with store.FileStore('exchanges', editable=True) as content:
        with session.ExanteSession() as exante:
            for exchange in ['NYSE', 'NASDAQ']:
                symbols = exante.symbols(exchange)
                content[exchange] = symbols


def reload_sp500():
    import pandas as pd
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    df = table[0]
    df = df.where(pd.notnull(df), None)
    dt = df.to_dict('split')
    with store.FileStore('S&P500', editable=True) as sp500:
        sp500['schema'] = dt['columns']
        sp500['data'] = dt['data']


if __name__ == '__main__':
    # update_series()
    # verify_series()
    reload_sp500()
