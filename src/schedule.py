import atexit
import logging
import sys

import orjson as json
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from src import load, tools

app = Flask(__name__)
app_log = app.logger
app_log.setLevel(logging.DEBUG)


def wsgi(environ, start_response):
    # gunicorn src.schedule:wsgi -b :8882
    return app(environ, start_response)


if 'gunicorn' in sys.modules:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
else:
    app.logger.handlers = []

scheduler = BackgroundScheduler(daemon=True)


@app.route("/schedule")
def list_scheduled_jobs():
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
    scheduler.shutdown()


@scheduler.scheduled_job('cron', hour=2)
def load_trading_data():
    load.reload_exchanges()
    load.series_update()
    load.series_verify()


scheduler.start()

if __name__ == "__main__":
    app.run()
