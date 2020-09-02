import argparse
from functools import lru_cache

from src import store, data_cache, log


@lru_cache(maxsize=1)
def get_args():
    choices = ['reload-exchanges', 'show-instrument-range', 'empty-series', 'update-series']
    parser = argparse.ArgumentParser(description='Trend Tools')
    parser.add_argument('--entry', required=True, choices=choices)
    args, argv = parser.parse_known_args()
    return args


def main():
    log.init(__file__, persist=False)

    args = get_args()
    if args.entry == 'reload-exchanges':
        data_cache.reload_exchanges()
    elif args.entry == 'show-instrument-range':
        data_cache.show_instrument_range()
    elif args.entry == 'empty-series':
        store.empty_series()
    elif args.entry == 'update-series':
        data_cache.update_series()


if __name__ == '__main__':
    main()
