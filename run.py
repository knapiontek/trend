#!/usr/bin/env python

import argparse
import logging

from src import store, load, web, log

LOG = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description='Trend Tools')

    parser.add_argument('--web', action='store_true')
    parser.add_argument('--reload-exchanges', action='store_true')

    parser.add_argument('--series-empty', action='store_true')
    parser.add_argument('--series-range', action='store_true')
    parser.add_argument('--series-update', action='store_true')
    parser.add_argument('--series-verify', action='store_true')

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

        if args.series_empty:
            store.series_empty()
        if args.series_range:
            load.series_range()
        if args.series_update:
            load.series_update()
        if args.series_verify:
            load.series_verify()
    except:
        LOG.exception('TrendApp failed')


if __name__ == '__main__':
    main()
