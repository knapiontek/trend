#!/usr/bin/env python

import argparse
import logging

from src import log, data, store, yahoo, exante, stooq

LOG = logging.getLogger(__name__)

EXCHANGE_ACTIONS = dict(erase=store.exchange_erase,
                        update=data.exchange_update)
ENGINES = dict(yahoo=yahoo, exante=exante, stooq=stooq)
ENGINE_ACTIONS = dict(erase=store.security_erase,
                      range=data.security_range,
                      update=data.security_update,
                      verify=data.security_verify,
                      clean=data.security_clean,
                      analyse=data.security_analyse)


def get_args():
    parser = argparse.ArgumentParser(description='Trend Tools')

    parser.add_argument('--web', action='store_true')
    parser.add_argument('--schedule', action='store_true')

    parser.add_argument('--exchange', nargs='+')
    parser.add_argument('--engine', nargs='+')
    parser.add_argument('--security', nargs='+')

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
            web.run_module(args.debug)
        if args.schedule:
            from src import schedule
            schedule.run_module(args.debug)
        for action_name in args.exchange or []:
            EXCHANGE_ACTIONS[action_name]()
        for engine_name in args.engine or []:
            for action_name in args.security or []:
                ENGINE_ACTIONS[action_name](ENGINES[engine_name])
    except KeyboardInterrupt:
        LOG.info('TrendApp interrupted')
    except:
        LOG.exception('TrendApp failed')
    else:
        LOG.info('TrendApp done')


if __name__ == '__main__':
    main()
