import atexit
import logging
import sys

import orjson as json
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from src import load, tools, log

LOG = logging.getLogger(__name__)

app = Flask(__name__)


def wsgi(environ, start_response):
    # gunicorn src.schedule:wsgi -b :8882
    return app(environ, start_response)


if 'gunicorn' in sys.modules:
    logging.getLogger('urllib3').setLevel(logging.INFO)
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.basicConfig(level=gunicorn_logger.level,
                        handlers=gunicorn_logger.handlers)

scheduler = BackgroundScheduler(daemon=True)
scheduler.start()


@app.route("/schedule/")
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
    return json.dumps(jobs, option=json.OPT_INDENT_2)


@atexit.register
def shutdown():
    LOG.info('Shutting down the scheduler')
    scheduler.shutdown()


@scheduler.scheduled_job('cron', hour=2)
def load_trading_data():
    LOG.info(f'Running scheduled task: {load_trading_data.__name__}')
    load.reload_exchanges()
    load.series_update()
    load.series_verify()


def run_schedule(debug: bool):
    return app.run(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_schedule(debug=debug)


if __name__ == "__main__":
    main()
