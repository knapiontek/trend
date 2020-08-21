import argparse
from functools import lru_cache

from src import store, session, resistance


@lru_cache(maxsize=1)
def get_args():
    choices = ['empty-db', 'load-exchanges', 'update-series', 'show-latest']
    parser = argparse.ArgumentParser(description='Trend Tools')
    parser.add_argument('--entry', required=True, choices=choices)
    args, argv = parser.parse_known_args()
    return args


def load_exchanges():
    with store.FileStore('static-data') as content:
        with session.ExanteSession() as exante:
            for exchange in ['NYSE', 'NASDAQ']:
                symbols = exante.symbols(exchange)
                content[exchange] = symbols


if __name__ == '__main__':
    args = get_args()
    if args.entry == 'empty-db':
        store.empty_series()
    elif args.entry == 'load-exchanges':
        load_exchanges()
    elif args.entry == 'show-latest':
        resistance.show_latest()
    elif args.entry == 'update-series':
        resistance.main()
