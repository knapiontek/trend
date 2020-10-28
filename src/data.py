import logging
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Any, Dict

import orjson as json
import pandas as pd

from src import store, tool, exante, log, config

LOG = logging.getLogger(__name__)

INDEX_SP500 = ('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', 0, 'Symbol', '')
INDEX_FTSE100 = ('https://en.wikipedia.org/wiki/FTSE_100_Index', 3, 'EPIC', '')
INDEX_WIG30 = ('https://en.wikipedia.org/wiki/WIG30', 0, 'Symbol', '')
INDEX_DAX30 = ('https://en.wikipedia.org/wiki/DAX', 3, 'Ticker symbol', '.DE')

EXCHANGE_INDEX = {'NYSE': INDEX_SP500,
                  'NASDAQ': INDEX_SP500,
                  'LSE': INDEX_FTSE100,
                  'XETRA': INDEX_DAX30,
                  'WSE': INDEX_WIG30}


def read_major_indices() -> Dict[str, List]:
    exchanges = {}
    for exchange_name, (url, index, column_name, suffix) in EXCHANGE_INDEX.items():
        if exchange_name not in exchanges:
            table = pd.read_html(url)
            symbols = table[index][column_name].to_list()
            exchanges[exchange_name] = [s.replace(suffix, '') for s in symbols]
    return exchanges


HEALTH_DEFAULT = {
    'health-exante': False,
    'health-yahoo': False,
    'health-stooq': False,
    'total': 0.0
}


def exchange_update():
    LOG.info(f'>> {exchange_update.__name__}')

    indices = read_major_indices()
    shortables = exante.read_shortables()

    store.exchange_clean()
    with store.Exchanges(editable=True) as db_exchanges:
        with exante.Session() as session:
            for name in config.ACTIVE_EXCHANGES:
                exchange_index = indices[name]
                instruments = session.instruments(name)
                documents = [
                    tool.Clazz(**instrument,
                               **HEALTH_DEFAULT,
                               shortable=instrument['symbol'] in shortables)
                    for instrument in instruments
                    if instrument['short-symbol'] in exchange_index
                ]
                db_exchanges += documents
                LOG.info(f'Imported {len(documents)} instruments from exchange {name}')


def series_range(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {series_range.__name__}({engine_name})')

    with engine.Series(tool.INTERVAL_1D) as db_series:
        time_range = {
            tr.symbol: [tool.ts_format(tr.min_ts), tool.ts_format(tr.max_ts)]
            for tr in db_series.time_range()
        }
        print(json.dumps(time_range, option=json.OPT_INDENT_2).decode('utf-8'))


def series_update(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {series_update.__name__}({engine_name})')

    interval = tool.INTERVAL_1D
    dt_from_default = datetime(2006, 12, 31, tzinfo=timezone.utc)

    with engine.Series(interval) as db_series:
        time_range = db_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')
        series_latest = {tr.symbol: tool.from_timestamp(tr.max_ts) for tr in time_range}

    for exchange_name in config.ACTIVE_EXCHANGES:
        with store.Exchanges() as db_exchanges:
            instruments = db_exchanges[exchange_name]

        LOG.info(f'Updating exchange: {exchange_name} instruments: {len(instruments)}')
        latest = {i.symbol: series_latest.get(i.symbol) or dt_from_default for i in instruments}

        with engine.Session() as session:
            with tool.Progress(f'series-update: {exchange_name}', latest) as progress:
                for symbol, dt_from in latest.items():
                    progress(symbol)
                    dt_to = tool.dt_last(exchange_name, interval, tool.utc_now())
                    for slice_from, slice_to in tool.time_slices(dt_from, dt_to, interval, 1024):
                        time_series = session.series(symbol, slice_from, slice_to, interval)

                        with engine.Series(interval, editable=True) as db_series:
                            db_series += time_series


def verify_symbol_series(engine: Any,
                         symbol: str,
                         dt_from: datetime, dt_to: datetime,
                         interval: timedelta) -> Tuple[List, List]:
    with engine.Series(interval) as db_series:
        series = db_series[symbol]

    _, exchange = tool.symbol_split(symbol)
    dt_holidays = tool.holidays(exchange)
    dt_series = {tool.from_timestamp(s.timestamp) for s in series}

    overlap = [tool.dt_format(d) for d in dt_series & dt_holidays]

    missing = []
    all_days = dt_series | dt_holidays
    start = dt_from
    while start <= dt_to:
        if start.weekday() in (0, 1, 2, 3, 4):
            if start not in all_days:
                missing.append(tool.dt_format(start))
        start += interval

    return overlap, missing


def series_verify(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {series_verify.__name__}({engine_name})')

    interval = tool.INTERVAL_1D
    health_name = f'health-{engine_name}-{tool.interval_name(interval)}'

    with engine.Series(interval) as db_series:
        time_range = db_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')

    with store.FileStore(health_name, editable=True) as health:
        with tool.Progress(health_name, time_range) as progress:
            for tr in time_range:
                progress(tr.symbol)
                overlap, missing = verify_symbol_series(engine,
                                                        tr.symbol,
                                                        tool.from_timestamp(tr.min_ts),
                                                        tool.from_timestamp(tr.max_ts),
                                                        interval)
                info = {}
                if overlap:
                    info['overlap'] = overlap
                if missing:
                    info['missing'] = missing
                if info:
                    health[tr.symbol] = info

    with store.FileStore(health_name) as health:
        with store.Exchanges(editable=True) as db_exchanges:
            for name in config.ACTIVE_EXCHANGES:
                instruments = db_exchanges[name]
                for i in instruments:
                    i[f'health-{engine_name}'] = i.symbol not in health
                db_exchanges |= instruments


def main():
    log.init(__file__, debug=True, to_screen=True)
    exchange_update()
    from src import stooq as engine
    series_range(engine)
    series_update(engine)
    series_verify(engine)


if __name__ == '__main__':
    main()
