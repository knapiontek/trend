import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Any, Dict

import orjson as json
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_fixed

from src import log, config, tool, flow, store, exante, analyse

LOG = logging.getLogger(__name__)

remote_retry = retry(stop=stop_after_attempt(2), wait=wait_fixed(100))

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


@remote_retry
def exchange_update():
    LOG.info(f'>> {exchange_update.__name__}')

    indices = read_major_indices()
    shortables = exante.read_shortables()

    with store.ExchangeSeries(editable=True) as exchange_series:
        with exante.Session() as session:
            for exchange_name in config.ACTIVE_EXCHANGES:
                exchange_index = indices[exchange_name]
                exchange_securities = {s.symbol: s for s in exchange_series[exchange_name]}
                new_documents = []
                old_documents = []
                for security in session.securities(exchange_name):
                    shortable = shortables.get(security.symbol, False)
                    if security.short_symbol in exchange_index:
                        if security.symbol in exchange_securities:
                            document = exchange_securities[security.symbol]
                            document.update(HEALTH_DEFAULT)
                            document.shortable = shortable
                            old_documents += [document]
                        else:
                            document = security
                            document.update(HEALTH_DEFAULT)
                            document.shortable = shortable
                            new_documents += [document]
                exchange_series |= old_documents
                LOG.info(f'Securities: {len(old_documents)} updated in the exchange: {exchange_name}')
                exchange_series += new_documents
                LOG.info(f'Securities: {len(new_documents)} imported to the exchange: {exchange_name}')


def security_range(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {security_range.__name__} engine: {engine_name}')

    with engine.SecuritySeries(tool.INTERVAL_1D) as security_series:
        time_range = {
            t.symbol: [tool.ts_format(t.min_ts), tool.ts_format(t.max_ts)]
            for t in security_series.time_range()
        }
        print(json.dumps(time_range, option=json.OPT_INDENT_2).decode('utf-8'))


@remote_retry
def security_update(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {security_update.__name__} engine: {engine_name}')

    interval = tool.INTERVAL_1D

    with engine.SecuritySeries(interval) as security_series:
        time_range = security_series.time_range()
        LOG.debug(f'Time range entries: {len(time_range)}')
        series_latest = {t.symbol: tool.from_timestamp(t.max_ts) for t in time_range}

    for exchange_name in config.ACTIVE_EXCHANGES:
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]

        security_latest = {s.symbol: series_latest.get(s.symbol) or config.datetime_from() for s in securities}

        with engine.Session() as session:
            with flow.Progress(f'security-update: {exchange_name}', security_latest) as progress:
                for symbol, dt_from in security_latest.items():
                    progress(symbol)
                    dt_to = tool.dt_last(exchange_name, interval, tool.utc_now())
                    for slice_from, slice_to in tool.time_slices(dt_from, dt_to, interval, 1024):
                        time_series = session.series(symbol, slice_from, slice_to, interval)

                        with engine.SecuritySeries(interval, editable=True) as security_series:
                            security_series += time_series

        LOG.info(f'Securities: {len(securities)} updated in the exchange: {exchange_name}')


def time_series_verify(engine: Any,
                       symbol: str,
                       dt_from: datetime, dt_to: datetime,
                       interval: timedelta) -> Tuple[List, List]:
    with engine.SecuritySeries(interval) as security_series:
        time_series = security_series[symbol]

    _, exchange = tool.symbol_split(symbol)
    dates = [tool.from_timestamp(s.timestamp) for s in time_series]
    holidays = tool.exchange_holidays(exchange)

    overlap = [tool.dt_format(d) for d in dates if d in holidays]

    missing = []
    start = dt_from
    while start <= dt_to:
        if start.weekday() in (0, 1, 2, 3, 4):
            if start not in dates and start not in holidays:
                missing.append(tool.dt_format(start))
        start += interval

    return overlap, missing


def security_verify(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {security_verify.__name__} engine: {engine_name}')

    interval = tool.INTERVAL_1D
    health_name = f'health-{engine_name}-{tool.interval_name(interval)}'

    with engine.SecuritySeries(interval) as security_series:
        time_range = security_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')

    with store.FileStore(health_name, editable=True) as health:
        health.update({e: {} for e in config.ACTIVE_EXCHANGES})
        with flow.Progress(health_name, time_range) as progress:
            for t in time_range:
                progress(t.symbol)
                short_symbol, exchange = tool.symbol_split(t.symbol)
                overlap, missing = time_series_verify(engine,
                                                      t.symbol,
                                                      tool.from_timestamp(t.min_ts),
                                                      tool.from_timestamp(t.max_ts),
                                                      interval)
                security_health = tool.Clazz()
                if overlap:
                    security_health.overlap = overlap
                if missing:
                    security_health.missing = missing
                if security_health:
                    health[exchange][short_symbol] = security_health

    with store.FileStore(health_name) as health:
        with store.ExchangeSeries(editable=True) as exchange_series:
            for name in config.ACTIVE_EXCHANGES:
                securities = exchange_series[name]
                for security in securities:
                    security[f'health-{engine_name}'] = security.symbol not in health
                exchange_series |= securities


def security_clean(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {security_clean.__name__} engine: {engine_name}')

    interval = tool.INTERVAL_1D

    for exchange_name in config.ACTIVE_EXCHANGES:
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]

        with flow.Progress(f'security-clean {exchange_name}', securities) as progress:
            for security in securities:
                progress(security.symbol)
                with engine.SecuritySeries(interval, editable=True) as security_series:
                    time_series = security_series[security.symbol]
                    analyse.clean(time_series)
                    security_series |= time_series

        LOG.info(f'Securities: {len(securities)} cleaned in the exchange: {exchange_name}')


def security_analyse(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {security_analyse.__name__} engine: {engine_name}')

    w_sizes = [50, 100, 200]
    interval = tool.INTERVAL_1D

    for exchange_name in config.ACTIVE_EXCHANGES:
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]

        with flow.Progress(f'security-analyse {exchange_name}', securities) as progress:
            for security in securities:
                progress(security.symbol)
                with engine.SecuritySeries(interval, editable=True) as security_series:
                    time_series = security_series[security.symbol]
                    for w_size in w_sizes:
                        analyse.sma(time_series, w_size)
                        analyse.vma(time_series, w_size)
                    security_series |= time_series

        LOG.info(f'Securities: {len(securities)} analysed in the exchange: {exchange_name}')


def main():
    log.init(__file__, debug=True, to_screen=True)

    exchange_update()

    import src.stooq as engine
    security_range(engine)
    security_update(engine)
    security_verify(engine)
    security_clean(engine)
    security_analyse(engine)


if __name__ == '__main__':
    main()
