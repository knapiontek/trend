from pprint import pprint

import src.config
from src import store, session, log, config


def receive_price_history(symbol: str):
    symbol_dict = {'symbol': symbol}
    with store.DBSeries(duration=config.DURATION_1D) as series:
        with session.ExanteSession() as exante:
            candles = exante.candles(symbol, batch_size=100, duration=src.config.DURATION_1D)
            series += [{**c, **symbol_dict} for c in candles]


def show_latest():
    with store.DBSeries(duration=config.DURATION_1D) as series:
        latest = series.latest()
        pprint(latest)


def main():
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
