from src import store, session


def load():
    with store.Store('static-data') as content:
        with session.ExanteSession() as exante:
            symbols = exante.symbols()
            content['symbols'] = symbols


if __name__ == '__main__':
    load()
