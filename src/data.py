import logging
from datetime import timedelta
from typing import List, Tuple, Any, Dict

import orjson as json
import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from src import log, config, tool, flow, store, exante, analyse, swings
from src.clazz import Clazz
from src.tool import DateTime

LOG = logging.getLogger(__name__)

remote_retry = retry(stop=stop_after_attempt(2),
                     wait=wait_fixed(100),
                     retry=retry_if_exception_type(requests.exceptions.ConnectionError))

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


@remote_retry
def exchange_update():
    LOG.info(f'>> {exchange_update.__name__}')

    indices = read_major_indices()
    shortables = exante.read_shortables()

    with store.ExchangeSeries(editable=True) as exchange_series:
        with exante.Session() as session:
            for exchange_name in config.EXCHANGES:
                exchange_index = indices[exchange_name]
                exchange_securities = {s.symbol: s for s in exchange_series[exchange_name]}
                new_documents = []
                existing_documents = []
                for security in session.securities(exchange_name):
                    shortable = shortables.get(security.symbol, False)
                    if security.short_symbol in exchange_index:
                        if security.symbol in exchange_securities:
                            document = exchange_securities[security.symbol]
                            document.shortable = shortable
                            existing_documents += [document]
                        else:
                            document = security
                            document.shortable = shortable
                            document.update({name: Clazz(health=False, profit=0.0, total=0.0, volume=0)
                                             for name in ('stooq_1d_test', 'yahoo_1d_test', 'exante_1d_test')})
                            document.update({name: False
                                             for name in ('stooq_1d_health', 'yahoo_1d_health', 'exante_1d_health')})
                            new_documents += [document]
                exchange_series *= existing_documents
                LOG.info(f'Securities: {len(existing_documents)} updated in the exchange: {exchange_name}')
                exchange_series += new_documents
                LOG.info(f'Securities: {len(new_documents)} imported to the exchange: {exchange_name}')


def security_range(engine: Any):
    interval = tool.INTERVAL_1D
    LOG.info(f'>> {security_range.__name__} source: {tool.source_name(engine, interval)}')

    with engine.SecuritySeries(interval) as security_series:
        print(json.dumps(security_series.time_range(),
                         option=json.OPT_INDENT_2,
                         default=tool.json_default).decode('utf-8'))


def security_update(engine: Any):
    security_update_by_interval(engine, tool.INTERVAL_1D)
    if engine == exante:
        security_update_by_interval(engine, tool.INTERVAL_1H)


@remote_retry
def security_update_by_interval(engine: Any, interval: timedelta):
    LOG.info(f'>> {security_update.__name__} source: {tool.source_name(engine, interval)}')

    default_range = Clazz(dt_to=config.datetime_from())
    with engine.SecuritySeries(interval) as security_series:
        time_range = security_series.time_range()
        LOG.debug(f'Time range entries: {len(time_range)}')

    for exchange_name in config.EXCHANGES:
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]

        with engine.Session() as session:
            with flow.Progress(f'security-update: {exchange_name}', securities) as progress:
                for security in securities:
                    progress(security.symbol)
                    dt_from = time_range.get(security.symbol, default_range).dt_to
                    dt_to = tool.last_session(exchange_name, interval, DateTime.now())
                    for slice_from, slice_to in tool.time_slices(dt_from, dt_to, interval, 4096):
                        time_series = session.series(security.symbol, slice_from, slice_to, interval)

                        with engine.SecuritySeries(interval, editable=True) as security_series:
                            security_series += time_series

        LOG.info(f'Securities: {len(securities)} updated in the exchange: {exchange_name}')


def time_series_verify(engine: Any,
                       symbol: str,
                       dt_from: DateTime, dt_to: DateTime,
                       interval: timedelta) -> Tuple[List, List]:
    with engine.SecuritySeries(interval) as security_series:
        time_series = security_series[symbol]

    _, exchange = tool.symbol_split(symbol)
    dates = [DateTime.from_timestamp(s.timestamp) for s in time_series]
    holidays = tool.exchange_holidays(exchange)

    overlap = [d.format() for d in dates if d in holidays]

    missing = []
    start = dt_from
    while start <= dt_to:
        if start.weekday() in (0, 1, 2, 3, 4):
            if start not in dates and start not in holidays:
                missing.append(start.format())
        start += interval

    return overlap, missing


def security_verify(engine: Any):
    interval = tool.INTERVAL_1D
    source_name = tool.source_name(engine, interval)
    health_name = tool.health_name(engine, interval)
    LOG.info(f'>> {security_verify.__name__} source: {source_name}')

    with engine.SecuritySeries(interval) as security_series:
        time_range = security_series.time_range()
        LOG.info(f'Time range entries: {len(time_range)}')

    with store.File(health_name, editable=True) as health:
        health.update({e: {} for e in config.EXCHANGES})
        with flow.Progress(health_name, time_range) as progress:
            for symbol, symbol_range in time_range.items():
                progress(symbol)
                short_symbol, exchange_name = tool.symbol_split(symbol)
                overlap, missing = time_series_verify(engine,
                                                      symbol,
                                                      symbol_range.dt_from,
                                                      symbol_range.dt_to,
                                                      interval)
                security_health = Clazz()
                if overlap:
                    security_health.overlap = overlap
                if missing:
                    security_health.missing = missing
                if security_health:
                    health[exchange_name][short_symbol] = security_health

    with store.File(health_name) as health:
        with store.ExchangeSeries(editable=True) as exchange_series:
            for exchange_name in config.EXCHANGES:
                securities = exchange_series[exchange_name]
                for security in securities:
                    short_symbol, _ = tool.symbol_split(security.symbol)
                    security_health = health[exchange_name].get(short_symbol, {})
                    missing_length = len(security_health.get('missing', []))
                    security[health_name] = missing_length < config.HEALTH_MISSING_LIMIT
                exchange_series *= securities


def security_clean(engine: Any):
    interval = tool.INTERVAL_1D
    source_name = tool.source_name(engine, interval)
    LOG.info(f'>> {security_clean.__name__} source: {source_name}')

    for exchange_name in config.EXCHANGES:
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]

        with flow.Progress(f'security-clean {exchange_name}', securities) as progress:
            for security in securities:
                progress(security.symbol)
                with engine.SecuritySeries(interval, editable=True) as security_series:
                    time_series = security_series[security.symbol]
                    analyse.clean(time_series)
                    security_series *= time_series

        LOG.info(f'Securities: {len(securities)} cleaned in the exchange: {exchange_name}')


def security_analyse(engine: Any):
    interval = tool.INTERVAL_1D
    w_sizes = [50, 100, 200]
    source_name = tool.source_name(engine, interval)
    result_name = tool.result_name(engine, interval, tool.ENV_TEST)
    LOG.info(f'>> {security_analyse.__name__} source: {source_name}')

    for exchange_name in config.EXCHANGES:
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]

        entries = []
        with flow.Progress(f'security-analyse {exchange_name}', securities) as progress:
            for security in securities:
                progress(security.symbol)

                with engine.SecuritySeries(interval, editable=True) as security_series:
                    time_series = security_series[security.symbol]
                    analyse.clean(time_series)
                    swings.calculate(time_series)
                    for w_size in w_sizes:
                        analyse.sma(time_series, w_size)
                        analyse.vma(time_series, w_size)
                    action = analyse.action(time_series)
                    security_series *= time_series

                    entry = security.entry(result_name)
                    entry[result_name] = action
                    entries += [entry]

        with store.ExchangeSeries(editable=True) as exchange_series:
            exchange_series |= entries

        LOG.info(f'Securities: {len(securities)} analysed in the exchange: {exchange_name}')


@tool.catch_exception(LOG)
def security_daily(engine: Any):
    security_update(engine)
    security_verify(engine)
    security_analyse(engine)


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
