from datetime import datetime
from pprint import pprint

from src import store, session, log, config


def receive_price_history(symbol: str):
    dt_from = datetime(2020, 1, 1, tzinfo=config.UTC_TZ)
    dt_to = datetime.now(tz=config.UTC_TZ)

    with store.DBSeries(duration=config.DURATION_1D) as db_series:
        with session.ExanteSession() as exante:
            time_series = exante.series(symbol, dt_from, dt_to, duration=config.DURATION_1D)
            db_series += time_series


def show_latest():
    with store.DBSeries(duration=config.DURATION_1D) as series:
        latest = series.latest()
        pprint(latest)


def update_series():
    log.init(__file__, persist=False)
    symbols = ['EUR/USD.E.FX',
               'EUR/GBP.E.FX',
               'XAG/USD.E.FX',
               'PKO.WSE',
               'KRU.WSE',
               'CDR.WSE',
               'XOM.NYSE',
               'TSLA.NASDAQ']
    for symbol in symbols:
        receive_price_history(symbol)


def reload_exchanges():
    with store.FileStore('static-data') as content:
        with session.ExanteSession() as exante:
            for exchange in ['NYSE', 'NASDAQ']:
                symbols = exante.symbols(exchange)
                content[exchange] = symbols
