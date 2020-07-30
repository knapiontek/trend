from src import store, session


def display_resistance(symbol: str):
    with store.Store('resistance') as content:
        with session.ExanteSession() as exante:
            candles = exante.candles(symbol, batch_size=1000, duration=session.DURATION_1D)

            content[symbol] = candles


if __name__ == '__main__':
    symbols = ['PKO.WSE', 'XOM.NYSE', 'EUR/USD.E.FX', 'TSLA.NASDAQ']
    for symbol in symbols:
        display_resistance(symbol)
