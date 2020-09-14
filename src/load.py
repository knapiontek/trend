import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from src import store, tools, holidays, exante, yahoo, log

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
    sp500 = list(tools.loop_it(read_sp500(), 'Symbol'))
    short_allowance = exante.read_short_allowance()
    with store.FileStore('exchanges', editable=True) as content:
        with exante.Session() as session:
            for exchange in ['NYSE', 'NASDAQ']:
                symbols = session.symbols(exchange)
                content[exchange] = [
                    {**s, **{'shortAllowed': short_allowance.get(s['symbolId']), 'total': 0.0}}
                    for s in symbols
                    if s['ticker'] in sp500
                ]
                LOG.info(f'Imported {len(content[exchange])} instruments from {exchange}')


def show_instrument_range():
    with yahoo.DBSeries(tools.INTERVAL_1D) as db_series:
        time_range = {
            symbol: [tools.ts_format(min_ts), tools.ts_format(max_ts)]
            for symbol, min_ts, max_ts in tools.tuple_it(db_series.time_range(), ('symbol', 'min_ts', 'max_ts'))
        }
        print(json.dumps(time_range, indent=2))


def update_series():
    with store.FileStore('exchanges') as exchanges:
        instruments = sum([v for k, v in exchanges.items()], [])
    LOG.info(f'Loaded instruments: {len(instruments)}')
    symbols = [i['symbolId'] for i in instruments]

    interval = tools.INTERVAL_1D
    delta = interval * 1000
    dt_from_default = datetime(2017, 12, 31, tzinfo=timezone.utc)
    dt_to = tools.dt_round(tools.utc_now(), interval)

    with yahoo.DBSeries(interval) as db_series:
        time_range = db_series.time_range()
    LOG.info(f'Loaded time-range entries: {len(time_range)}')

    latest = {r['symbol']: tools.from_timestamp(r['max_ts']) for r in time_range}
    instruments_latest = {s: latest.get(s) or dt_from_default for s in symbols}

    with yahoo.Session() as session:
        with tools.Progress('series-update', instruments_latest) as progress:
            for symbol, dt_from in instruments_latest.items():
                progress(symbol)
                for slice_from, slice_to in tools.time_slices(dt_from, dt_to, delta, interval):
                    time_series = session.series(symbol, slice_from, slice_to, interval)

                    with yahoo.DBSeries(interval, editable=True) as db_series:
                        db_series += time_series


def verify_instrument(symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> Dict[str, List]:
    health = {}
    with yahoo.DBSeries(interval) as db_series:
        series = db_series[symbol]

    exchange = symbol.split('.')[-1]
    dt_holidays = {tools.dt_parse(d) for d in holidays.HOLIDAYS[exchange]}
    db_dates = {tools.from_timestamp(s['timestamp']) for s in series}

    overlap = db_dates & dt_holidays
    if overlap:
        health['overlap'] = [tools.dt_format(d) for d in overlap]
    all_days = db_dates | dt_holidays

    missing = []
    start = dt_from
    while start < dt_to:
        if start.weekday() in (0, 1, 2, 3, 4):
            if start not in all_days:
                missing.append(tools.dt_format(start))
        start += interval
    if missing:
        health['missing'] = missing

    return health


def verify_series():
    interval = tools.INTERVAL_1D
    with yahoo.DBSeries(interval) as series:
        time_range = series.time_range()
    LOG.info(f'Loaded time-range entries: {len(time_range)}')

    name = f'series-yahoo-{tools.interval_name(interval)}-health'
    with store.FileStore(name, editable=True) as health:
        with tools.Progress(name, time_range) as progress:
            for symbol, ts_from, ts_to in tools.tuple_it(time_range, ('symbol', 'min_ts', 'max_ts')):
                progress(symbol)
                symbol_health = verify_instrument(symbol,
                                                  tools.from_timestamp(ts_from),
                                                  tools.from_timestamp(ts_to),
                                                  interval)
                if symbol_health:
                    health[symbol] = symbol_health


def main():
    log.init(__file__, debug=True, to_screen=True)
    # show_instrument_range()
    # reload_exchanges()
    update_series()
    # verify_series()


if __name__ == '__main__':
    main()
