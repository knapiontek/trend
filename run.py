#!/usr/bin/env python

import argparse
import logging

from src import store, load, web, log

LOG = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description='Trend Tools')

    parser.add_argument('--web', action='store_true')
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
    try:
        args = get_args()
        log.init(__file__, debug=args.debug, to_screen=args.log_to_screen, to_file=args.log_to_file)

        if args.web:
            web.run_dash(args.debug)
        if args.reload_exchanges:
            load.reload_exchanges()
        if args.show_instrument_range:
            load.show_instrument_range()
        if args.empty_series:
            store.empty_series()
        if args.update_series:
            load.update_series()
        if args.verify_series:
            load.verify_series()
    except:
        LOG.exception('trend-app failed')


if __name__ == '__main__':
    main()
