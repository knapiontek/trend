import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple

import orjson as json

from src import store, tools, exante, log, config

LOG = logging.getLogger(__name__)


def read_snp500() -> Dict:
    import pandas as pd
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    df = table[0]
    df = df.where(pd.notnull(df), None)
    dt = df.to_dict('split')
    return {
        'schema': dt['columns'],
        'data': dt['data']
    }


def exchange_update():
    LOG.info(f'>> {exchange_update.__name__}')

    snp500 = list(tools.loop_it(read_snp500(), 'Symbol'))
    shortables = exante.read_shortables()

    store.exchange_empty()
    with store.Exchanges(editable=True) as db_exchanges:
        with exante.Session() as session:
            for name in config.ACTIVE_EXCHANGES:
                instruments = session.instruments(name)
                documents = [
                    dict(instrument,
                         shortable=instrument['symbol'] in shortables,
                         health=False,
                         total=0.0)
                    for instrument in instruments
                    if instrument['short-symbol'] in snp500
                ]
                db_exchanges += documents
                LOG.info(f'Imported {len(documents)} instruments from exchange {name}')


def series_range(data_module):
    LOG.info(f'>> {series_range.__name__}')

    with data_module.Series(tools.INTERVAL_1D) as db_series:
        time_range = {
            symbol: [tools.ts_format(min_ts), tools.ts_format(max_ts)]
            for symbol, min_ts, max_ts in tools.tuple_it(db_series.time_range(), ('symbol', 'min_ts', 'max_ts'))
        }
        print(json.dumps(time_range, option=json.OPT_INDENT_2).decode('utf-8'))


def series_update(data_module):
    LOG.info(f'>> {series_update.__name__}')

    interval = tools.INTERVAL_1D
    dt_from_default = datetime(2017, 12, 31, tzinfo=timezone.utc)

    with data_module.Series(interval) as db_series:
        time_range = db_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')
        series_latest = {tr['symbol']: tools.from_timestamp(tr['max_ts']) for tr in time_range}

    for exchange_name in config.ACTIVE_EXCHANGES:
        with store.Exchanges() as db_exchanges:
            instruments = db_exchanges[exchange_name]

        LOG.info(f'Updating exchange: {exchange_name} instruments: {len(instruments)}')
        symbols = tools.loop_it(instruments, 'symbol')
        latest = {s: series_latest.get(s) or dt_from_default for s in symbols}

        with data_module.Session() as session:
            with tools.Progress(f'series-update: {exchange_name}', latest) as progress:
                for symbol, dt_from in latest.items():
                    progress(symbol)
                    dt_to = tools.dt_last(exchange_name, interval)
                    for slice_from, slice_to in tools.time_slices(dt_from, dt_to, interval, 1024):
                        time_series = session.series(symbol, slice_from, slice_to, interval)

                        with data_module.Series(interval, editable=True) as db_series:
                            db_series += time_series


def verify_symbol_series(data_module,
                         symbol: str,
                         dt_from: datetime, dt_to: datetime,
                         interval: timedelta) -> Tuple[List, List]:
    with data_module.Series(interval) as db_series:
        series = db_series[symbol]

    _, exchange = tools.symbol_split(symbol)
    dt_holidays = tools.holidays(exchange)
    dt_series = {tools.from_timestamp(ts) for ts in tools.loop_it(series, 'timestamp')}

    overlap = [tools.dt_format(d) for d in dt_series & dt_holidays]

    missing = []
    all_days = dt_series | dt_holidays
    start = dt_from
    while start <= dt_to:
        if start.weekday() in (0, 1, 2, 3, 4):
            if start not in all_days:
                missing.append(tools.dt_format(start))
        start += interval

    return overlap, missing


def series_verify(data_module):
    LOG.info(f'>> {series_verify.__name__}')

    interval = tools.INTERVAL_1D
    health_name = f'series-{tools.module_name(__name__)}-{tools.interval_name(interval)}-health'

    with data_module.Series(interval) as db_series:
        time_range = db_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')

    with store.FileStore(health_name, editable=True) as health:
        with tools.Progress(health_name, time_range) as progress:
            for symbol, ts_from, ts_to in tools.tuple_it(time_range, ('symbol', 'min_ts', 'max_ts')):
                progress(symbol)
                overlap, missing = verify_symbol_series(data_module,
                                                        symbol,
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

    with store.FileStore(health_name) as health:
        with store.Exchanges(editable=True) as db_exchanges:
            for name in config.ACTIVE_EXCHANGES:
                db_exchanges |= [
                    dict(instrument, health=instrument['symbol'] not in health)
                    for instrument in db_exchanges[name]
                ]


def main():
    log.init(__file__, debug=True, to_screen=True)
    exchange_update()
    from src import yahoo
    series_range(yahoo)
    series_update(yahoo)
    series_verify(yahoo)


if __name__ == '__main__':
    main()
