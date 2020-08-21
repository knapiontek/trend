import argparse
from functools import lru_cache

from src import store, data_cache


@lru_cache(maxsize=1)
def get_args():
    choices = ['empty-db', 'reload-exchanges', 'update-series', 'show-latest']
    parser = argparse.ArgumentParser(description='Trend Tools')
    parser.add_argument('--entry', required=True, choices=choices)
    args, argv = parser.parse_known_args()
    return args


if __name__ == '__main__':
    args = get_args()
    if args.entry == 'empty-db':
        store.empty_series()
    elif args.entry == 'reload-exchanges':
        data_cache.reload_exchanges()
    elif args.entry == 'show-latest':
        data_cache.show_latest()
    elif args.entry == 'update-series':
        data_cache.update_series()
