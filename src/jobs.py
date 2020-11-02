import logging
import sys
import threading
import time

import orjson as json
import schedule
from flask import Flask, request

from src import data, log, yahoo, exante, stooq, config, tool

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


schedule.every().day.at('02:30').do(load_trading_data)


def run_scheduled_jobs():
    while True:
        schedule.run_pending()
        time.sleep(60)


@app.route("/schedule/", methods=['GET', 'POST'])
def schedule_update_job():
    if request.method == 'POST':
        LOG.info(f'Scheduling {load_trading_data.__name__}')
        thread = threading.Thread(target=load_trading_data)
        thread.start()

    LOG.info('Listing scheduled tasks')
    jobs = [
        {
            'name': job.job_func.__name__,
            'last_run': tool.dt_format(job.last_run) if job.last_run else None,
            'next_run': tool.dt_format(job.next_run)
        }
        for job in schedule.jobs
    ]
    return json.dumps(jobs, option=json.OPT_INDENT_2).decode('utf-8')


def run_schedule(debug: bool):
    thread = threading.Thread(target=run_scheduled_jobs)
    thread.start()
    return app.run(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_schedule(debug=debug)


if __name__ == "__main__":
    main()
