import atexit
import logging
import sys
from datetime import timedelta

import orjson as json
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from src import data, tools, log, yahoo, exante, stooq

LOG = logging.getLogger(__name__)

app = Flask(__name__)


def wsgi(environ, start_response):
    # gunicorn src.schedule:wsgi -b :8882
    return app(environ, start_response)


if 'gunicorn' in sys.modules:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.basicConfig(level=gunicorn_logger.level, handlers=gunicorn_logger.handlers)
    logging.getLogger('urllib3').setLevel(logging.INFO)

scheduler = BackgroundScheduler(daemon=True)
scheduler.start()


@app.route("/list-scheduled-jobs/")
def list_scheduled_jobs():
    LOG.info('Listing scheduled tasks')
    jobs = [
        {
            'name': job.name,
            'next-run-at': tools.dt_format(job.next_run_time),
            'pending': job.pending
        }
        for job in scheduler.get_jobs()
    ]
    return json.dumps(jobs, option=json.OPT_INDENT_2).decode('utf-8')


@app.route("/schedule-job/")
def schedule_update_job():
    LOG.info(f'Scheduling {load_trading_data.__name__}')
    dt = tools.utc_now() + timedelta(minutes=1)
    scheduler.add_job(load_trading_data, 'date', hour=dt.hour, minute=dt.minute, second=dt.second)
    return list_scheduled_jobs()


@atexit.register
def shutdown():
    LOG.info('Shutting down the scheduler')
    scheduler.shutdown()


@scheduler.scheduled_job('cron', hour=10, minute=30)
def load_trading_data():
    LOG.info(f'Running scheduled task: {load_trading_data.__name__}')
    data.exchange_update()

    for engine in (yahoo, exante, stooq):
        data.series_update(engine)
        data.series_verify(engine)


def run_schedule(debug: bool):
    return app.run(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_schedule(debug=debug)


if __name__ == "__main__":
    main()
