import logging
import sys
import threading

import eventlet
import orjson as json
from flask import Flask, request

from src import data, log, yahoo, exante, stooq, config

LOG = logging.getLogger(__name__)

app = Flask(__name__, static_folder=config.ASSETS_PATH.as_posix())


def wsgi(environ, start_response):
    # gunicorn src.schedule:wsgi -b :8882
    return app(environ, start_response)


if 'gunicorn' in sys.modules:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.basicConfig(level=gunicorn_logger.level, handlers=gunicorn_logger.handlers)
    logging.getLogger('urllib3').setLevel(logging.INFO)


def load_trading_data():
    LOG.info(f'Running scheduled task: {load_trading_data.__name__}')

    data.exchange_update()

    for engine in (yahoo, exante, stooq):
        data.security_update(engine)
        data.security_verify(engine)
        data.security_analyse(engine)


@app.route("/schedule/", methods=['GET', 'POST'])
def schedule_update_job():
    if request.method == 'POST':
        LOG.info(f'Scheduling {load_trading_data.__name__}')
        eventlet.spawn(load_trading_data)

    LOG.info('Listing scheduled tasks')
    threads = [
        {
            'name': thread.name,
            'alive': thread.is_alive(),
            'daemon': thread.daemon
        }
        for thread in threading.enumerate()
    ]
    return json.dumps(threads, option=json.OPT_INDENT_2).decode('utf-8')


def run_schedule(debug: bool):
    return app.run(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_schedule(debug=debug)


if __name__ == "__main__":
    main()
