from src import store, session


def display_resistance(symbol: str):
    with store.Store('resistance') as content:
        with session.ExanteSession() as exante:
            candles = exante.candles(symbol, 10, 60)

            content[symbol] = candles


if __name__ == '__main__':
    # symbol = 'EUR/USD.E.FX'
    symbol = 'PKO.WSE'
    display_resistance(symbol)
