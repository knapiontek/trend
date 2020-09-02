import argparse
from functools import lru_cache

from src import store, data_cache, log


@lru_cache(maxsize=1)
def get_args():
    parser = argparse.ArgumentParser(description='Trend Tools')

    parser.add_argument('--reload-exchanges', action='store_true')
    parser.add_argument('--show-instrument-range', action='store_true')
    parser.add_argument('--empty-series', action='store_true')
    parser.add_argument('--update-series', action='store_true')
    parser.add_argument('--verify-series', action='store_true')

    parser.add_argument('--log-to-file', action='store_true')
    parser.add_argument('--log-to-screen', action='store_true')
    parser.add_argument('--debug', action='store_true')

    args, argv = parser.parse_known_args()
    return args


def main():
    args = get_args()

    log.init(__file__, to_screen=args.log_to_screen, to_file=args.log_to_file, debug=args.debug)

    if args.reload_exchanges:
        data_cache.reload_exchanges()
    elif args.show_instrument_range:
        data_cache.show_instrument_range()
    elif args.empty_series:
        store.empty_series()
    elif args.update_series:
        data_cache.update_series()
    elif args.verify_series:
        data_cache.verify_series()


if __name__ == '__main__':
    main()
