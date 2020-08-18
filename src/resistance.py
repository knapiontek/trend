from src import store, session, log


def display_resistance(symbol: str):
    with store.Store('resistance') as content:
        with session.ExanteSession() as exante:
            candles = exante.candles(symbol, batch_size=100, duration=session.DURATION_1D)

            content[symbol] = candles


def main():
    log.init(__file__, persist=True)
    symbols = ['PKO.WSE', 'KRU.WSE', 'CDR.WSE', 'XOM.NYSE', 'EUR/USD.E.FX', 'TSLA.NASDAQ']
    for symbol in symbols:
        display_resistance(symbol)


if __name__ == '__main__':
    main()
