import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple

import orjson as json

from src import store, tools, exante, yahoo, log

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
    LOG.info(f'>> {reload_exchanges.__name__}')

    boolean = ['-', '+']
    sp500 = list(tools.loop_it(read_sp500(), 'Symbol'))
    short_allowance = exante.read_short_allowance()

    with store.FileStore('exchanges', editable=True) as content:
        with exante.Session() as session:
            for exchange in ['NYSE', 'NASDAQ']:
                symbols = session.symbols(exchange)
                content[exchange] = [
                    {
                        **s,
                        **{
                            'shortAllowed': boolean[short_allowance.get(s['symbolId'])],
                            'health': boolean[False],
                            'total': 0.0
                        }
                    }
                    for s in symbols
                    if s['ticker'] in sp500
                ]
                LOG.info(f'Imported {len(content[exchange])} instruments from {exchange}')


def series_range():
    LOG.info(f'>> {series_range.__name__}')

    with yahoo.TimeSeries(tools.INTERVAL_1D) as db_series:
        time_range = {
            symbol: [tools.ts_format(min_ts), tools.ts_format(max_ts)]
            for symbol, min_ts, max_ts in tools.tuple_it(db_series.time_range(), ('symbol', 'min_ts', 'max_ts'))
        }
        print(json.dumps(time_range, option=json.OPT_INDENT_2).decode('utf-8'))


def series_update():
    LOG.info(f'>> {series_update.__name__}')

    interval = tools.INTERVAL_1D
    dt_from_default = datetime(2017, 12, 31, tzinfo=timezone.utc)

    with yahoo.TimeSeries(interval) as db_series:
        time_range = db_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')
        latest = {r['symbol']: tools.from_timestamp(r['max_ts']) for r in time_range}

    with store.FileStore('exchanges') as exchanges:
        for exchange, instruments in exchanges.items():
            LOG.info(f'Updating exchange: {exchange} instruments: {len(instruments)}')
            symbols = [i['symbolId'] for i in instruments]

            instruments_latest = {s: latest.get(s) or dt_from_default for s in symbols}

            with yahoo.Session() as session:
                with tools.Progress(f'series-update: {exchange}', instruments_latest) as progress:
                    for symbol, dt_from in instruments_latest.items():
                        progress(symbol)
                        dt_to = tools.dt_last(exchange, interval)
                        for slice_from, slice_to in tools.time_slices(dt_from, dt_to, interval, 1024):
                            time_series = session.series(symbol, slice_from, slice_to, interval)

                            with yahoo.TimeSeries(interval, editable=True) as db_series:
                                db_series += time_series


def verify_symbol_series(symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> Tuple[List, List]:
    with yahoo.TimeSeries(interval) as db_series:
        series = db_series[symbol]

    exchange = symbol.split('.')[-1]
    dt_holidays = tools.holidays(exchange)
    db_dates = {tools.from_timestamp(s['timestamp']) for s in series}

    overlap = [tools.dt_format(d) for d in db_dates & dt_holidays]

    missing = []
    all_days = db_dates | dt_holidays
    start = dt_from
    while start <= dt_to:
        if start.weekday() in (0, 1, 2, 3, 4):
            if start not in all_days:
                missing.append(tools.dt_format(start))
        start += interval

    return overlap, missing


def series_verify():
    LOG.info(f'>> {series_verify.__name__}')

    interval = tools.INTERVAL_1D
    with yahoo.TimeSeries(interval) as db_series:
        time_range = db_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')

    health_name = f'series-yahoo-{tools.interval_name(interval)}-health'
    with store.FileStore(health_name, editable=True) as health:
        with tools.Progress(health_name, time_range) as progress:
            for symbol, ts_from, ts_to in tools.tuple_it(time_range, ('symbol', 'min_ts', 'max_ts')):
                progress(symbol)
                overlap, missing = verify_symbol_series(symbol,
                                                        tools.from_timestamp(ts_from),
                                                        tools.from_timestamp(ts_to),
                                                        interval)
                info = {}
                if overlap:
                    info['overlap'] = overlap
                if missing:
                    info['missing'] = missing
                if info:
                    health[symbol] = info

    # update exchanges with health
    boolean = ['-', '+']
    with store.FileStore(health_name) as health:
        with store.FileStore('exchanges', editable=True) as exchanges:
            for exchange, instruments in exchanges.items():
                for instrument in instruments:
                    symbol = instrument['symbolId']
                    instrument['health'] = boolean[bool(not health.get(symbol))]


def main():
    log.init(__file__, debug=True, to_screen=True)
    reload_exchanges()
    series_range()
    series_update()
    series_verify()


if __name__ == '__main__':
    main()
