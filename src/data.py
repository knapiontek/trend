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
    with store.ExchangeSeries(editable=True) as exchange_series:
        with exante.Session() as session:
            for name in config.ACTIVE_EXCHANGES:
                exchange_index = indices[name]
                securities = session.securities(name)
                documents = [
                    tool.Clazz(**security,
                               **HEALTH_DEFAULT,
                               shortable=security['symbol'] in shortables)
                    for security in securities
                    if security['short-symbol'] in exchange_index
                ]
                exchange_series += documents
                LOG.info(f'Securities {len(documents)} imported from the exchange {name}')


def security_range(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {security_range.__name__}({engine_name})')

    with engine.SecuritySeries(tool.INTERVAL_1D) as security_series:
        time_range = {
            t.symbol: [tool.ts_format(t.min_ts), tool.ts_format(t.max_ts)]
            for t in security_series.time_range()
        }
        print(json.dumps(time_range, option=json.OPT_INDENT_2).decode('utf-8'))


def security_update(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {security_update.__name__}({engine_name})')

    interval = tool.INTERVAL_1D
    dt_from_default = datetime(2006, 12, 31, tzinfo=timezone.utc)

    with engine.SecuritySeries(interval) as security_series:
        time_range = security_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')
        series_latest = {t.symbol: tool.from_timestamp(t.max_ts) for t in time_range}

    for exchange_name in config.ACTIVE_EXCHANGES:
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]

        LOG.info(f'Updating exchange: {exchange_name} securities: {len(securities)}')
        security_latest = {s.symbol: series_latest.get(s.symbol) or dt_from_default for s in securities}

        with engine.Session() as session:
            with tool.Progress(f'series-update: {exchange_name}', security_latest) as progress:
                for symbol, dt_from in security_latest.items():
                    progress(symbol)
                    dt_to = tool.dt_last(exchange_name, interval, tool.utc_now())
                    for slice_from, slice_to in tool.time_slices(dt_from, dt_to, interval, 1024):
                        time_series = session.series(symbol, slice_from, slice_to, interval)

                        with engine.SecuritySeries(interval, editable=True) as security_series:
                            security_series += time_series


def time_series_verify(engine: Any,
                       symbol: str,
                       dt_from: datetime, dt_to: datetime,
                       interval: timedelta) -> Tuple[List, List]:
    with engine.SecuritySeries(interval) as security_series:
        time_series = security_series[symbol]

    _, exchange = tool.symbol_split(symbol)
    holidays = tool.holidays(exchange)
    dates = {tool.from_timestamp(s.timestamp) for s in time_series}

    overlap = [tool.dt_format(d) for d in dates & holidays]

    missing = []
    all_days = dates | holidays
    start = dt_from
    while start <= dt_to:
        if start.weekday() in (0, 1, 2, 3, 4):
            if start not in all_days:
                missing.append(tool.dt_format(start))
        start += interval

    return overlap, missing


def security_verify(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {security_verify.__name__}({engine_name})')

    interval = tool.INTERVAL_1D
    health_name = f'health-{engine_name}-{tool.interval_name(interval)}'

    with engine.SecuritySeries(interval) as security_series:
        time_range = security_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')

    with store.FileStore(health_name, editable=True) as health:
        with tool.Progress(health_name, time_range) as progress:
            for t in time_range:
                progress(t.symbol)
                overlap, missing = time_series_verify(engine,
                                                      t.symbol,
                                                      tool.from_timestamp(t.min_ts),
                                                      tool.from_timestamp(t.max_ts),
                                                      interval)
                info = {}
                if overlap:
                    info['overlap'] = overlap
                if missing:
                    info['missing'] = missing
                if info:
                    health[t.symbol] = info

    with store.FileStore(health_name) as health:
        with store.ExchangeSeries(editable=True) as exchange_series:
            for name in config.ACTIVE_EXCHANGES:
                securities = exchange_series[name]
                for security in securities:
                    security[f'health-{engine_name}'] = security.symbol not in health
                exchange_series |= securities


def main():
    log.init(__file__, debug=True, to_screen=True)
    exchange_update()
    from src import stooq as engine
    security_range(engine)
    security_update(engine)
    security_verify(engine)


if __name__ == '__main__':
    main()
