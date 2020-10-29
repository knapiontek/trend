#!/usr/bin/env python

import argparse
import logging

from src import log, data, store, yahoo, exante, stooq

LOG = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(description='Trend Tools')

    parser.add_argument('--web', action='store_true')
    parser.add_argument('--schedule', action='store_true')

    parser.add_argument('--exchange-clean', action='store_true')
    parser.add_argument('--exchange-update', action='store_true')

    parser.add_argument('--engines', nargs='+', required=True)

    parser.add_argument('--security-clean', action='store_true')
    parser.add_argument('--security-range', action='store_true')
    parser.add_argument('--security-update', action='store_true')
    parser.add_argument('--security-verify', action='store_true')

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

        if args.exchange_clean:
            store.exchange_clean()
        if args.exchange_update:
            data.exchange_update()

        engines = dict(yahoo=yahoo, exante=exante, stooq=stooq)
        for datum in args.engines:
            engine = engines[datum]
            if args.security_clean:
                store.security_clean(engine)
            if args.security_range:
                data.security_range(engine)
            if args.security_update:
                data.security_update(engine)
            if args.security_verify:
                data.security_verify(engine)
    except:
        LOG.exception('TrendApp failed')


if __name__ == '__main__':
    main()
