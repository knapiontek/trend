#!/usr/bin/env python

import argparse
import logging

from src import log, load, store

LOG = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description='Trend Tools')

    parser.add_argument('-w', '--web', action='store_true')
    parser.add_argument('-c', '--schedule', action='store_true')
    parser.add_argument('-x', '--reload-exchanges', action='store_true')

    parser.add_argument('-e', '--series-empty', action='store_true')
    parser.add_argument('-r', '--series-range', action='store_true')
    parser.add_argument('-u', '--series-update', action='store_true')
    parser.add_argument('-v', '--series-verify', action='store_true')

    parser.add_argument('-f', '--log-to-file', action='store_true')
    parser.add_argument('-s', '--log-to-screen', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')

    args, argv = parser.parse_known_args()
    return args


def main():
    args = get_args()
    log.init(__file__, debug=args.debug, to_screen=args.log_to_screen, to_file=args.log_to_file)

    try:
        if args.web:
            from src import web
            web.run_dash(args.debug)
        if args.schedule:
            from src import schedule
            schedule.run_schedule(args.debug)

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
