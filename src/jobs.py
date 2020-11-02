import logging
import sys
import threading
import time

import orjson as json
import schedule
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
        thread = threading.Thread(target=load_trading_data, name=load_trading_data.__name__)
        thread.start()

    LOG.info('Listing threads')
    threads = [
        {
            'name': thread.name,
            'daemon': thread.daemon,
            'alive': thread.is_alive()
        }
        for thread in threading.enumerate()
    ]
    LOG.info('Listing scheduled jobs')
    jobs = [
        {
            'name': job.job_func.__name__,
            'last_run': job.last_run,
            'next_run': job.next_run
        }
        for job in schedule.jobs
    ]
    return json.dumps(dict(threads=threads, jobs=jobs), option=json.OPT_INDENT_2).decode('utf-8')


schedule.every().day.at('02:30').do(load_trading_data)


def run_scheduled_jobs():
    while True:
        schedule.run_pending()
        time.sleep(60)


def run_schedule(debug: bool):
    thread = threading.Thread(target=run_scheduled_jobs, name=run_scheduled_jobs.__name__)
    thread.start()
    return app.run(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_schedule(debug=debug)


if __name__ == "__main__":
    main()
