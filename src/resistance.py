import src.config
from src import store, session, log, config


def receive_price_history(symbol: str):
    with store.DBSeries(symbol=symbol, duration=config.DURATION_1D) as series:
        with session.ExanteSession() as exante:
            candles = exante.candles(symbol, batch_size=1000, duration=src.config.DURATION_1D)
            series += candles


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
    symbols = ['XOM.NYSE']
    for symbol in symbols:
        receive_price_history(symbol)


if __name__ == '__main__':
    main()
