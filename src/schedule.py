import logging
import sys
import threading
import time

import orjson as json
from flask import Flask, request

from src import data, log, yahoo, exante, stooq, config

LOG = logging.getLogger(__name__)

app = Flask(__name__, static_folder=config.ASSETS_PATH.as_posix())


def wsgi(environ, start_response):
    # gunicorn src.schedule:wsgi -b :8882
    return app(environ, start_response)


def execute(function):
    thread = threading.Thread(target=function, name=function.__name__)
    thread.start()


def run_scheduled_jobs():
    tasks = [(2, 30)]
    while True:
        for hours, minutes in tasks:
            load_trading_data()
        time.sleep(60)


if 'gunicorn' in sys.modules:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.basicConfig(level=gunicorn_logger.level, handlers=gunicorn_logger.handlers)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    execute(run_scheduled_jobs)


def load_trading_data():
    try:
        LOG.info(f'Running scheduled task: {load_trading_data.__name__}')
        data.exchange_update()
        for engine in (yahoo, exante, stooq):
            data.security_update(engine)
            data.security_verify(engine)
            data.security_analyse(engine)
    except:
        LOG.exception(f'{load_trading_data.__name__} failed')
    else:
        LOG.info(f'{load_trading_data.__name__} done')


@app.route("/schedule/", methods=['GET', 'POST'])
def schedule_update_job():
    if request.method == 'POST':
        LOG.info(f'Scheduling {load_trading_data.__name__}')
        execute(load_trading_data)

    LOG.info('Listing threads')
    threads = [
        {
            'name': thread.name,
            'daemon': thread.daemon,
            'alive': thread.is_alive()
        }
        for thread in threading.enumerate()
    ]
    return json.dumps(threads, option=json.OPT_INDENT_2).decode('utf-8')


def run_tasks(debug: bool):
    execute(run_scheduled_jobs)
    return app.run(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_tasks(debug=debug)


if __name__ == "__main__":
    main()
