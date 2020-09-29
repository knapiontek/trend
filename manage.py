#!/usr/bin/env python

import argparse
import logging

from src import log, data, store

LOG = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description='Trend Tools')

    parser.add_argument('--web', action='store_true')
    parser.add_argument('--schedule', action='store_true')

    parser.add_argument('--exchange-empty', action='store_true')
    parser.add_argument('--exchange-update', action='store_true')

    parser.add_argument('--data', nargs='+', required=True)

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
    args = get_args()
    log.init(__file__, debug=args.debug, to_screen=args.log_to_screen, to_file=args.log_to_file)

    try:
        if args.web:
            from src import web
            web.run_dash(args.debug)
        if args.schedule:
            from src import schedule
            schedule.run_schedule(args.debug)

        if args.exchange_empty:
            store.exchange_empty()
        if args.exchange_update:
            data.exchange_update()

        from src import yahoo, exante, stooq
        modules = dict(yahoo=yahoo, exante=exante, stooq=stooq)
        for datum in args.data:
            module = modules[datum]
            if args.series_empty:
                store.series_empty(module)
            if args.series_range:
                data.series_range(module)
            if args.series_update:
                data.series_update(module)
            if args.series_verify:
                data.series_verify(module)
    except:
        LOG.exception('TrendApp failed')


if __name__ == '__main__':
    main()
