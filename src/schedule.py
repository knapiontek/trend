import logging
import sys
import threading
import time
from datetime import timedelta

import orjson as json
from flask import Flask, request

from src import data, log, yahoo, exante, stooq, config, tool

LOG = logging.getLogger(__name__)

app = Flask(__name__, static_folder=config.ASSETS_PATH.as_posix())


def wsgi(environ, start_response):
    # gunicorn src.schedule:wsgi -b :8882
    return app(environ, start_response)


@tool.catch_exception(LOG)
def maintain_task():
    data.exchange_update()
    for engine in (yahoo, exante, stooq):
        data.security_update(engine)
        data.security_verify(engine)
        data.security_analyse(engine)


TASKS = [tool.Clazz(hour=2, minute=30, next_run=None, last_run=None, running=False, function=maintain_task)]


def run_scheduled_tasks():
    for task in TASKS:
        utc_now = tool.utc_now()
        task.next_run = utc_now.replace(hour=task.hour, minute=task.minute)
        if task.next_run < utc_now:
            task.next_run += tool.INTERVAL_1D

    while True:
        for task in TASKS:
            if task.next_run < tool.utc_now():
                task.next_run += tool.INTERVAL_1D
                try:
                    LOG.info(f'Task: {task.function.__name__} started')
                    task.running = True
                    task.function()
                except:
                    pass
                finally:
                    task.running = False
                    task.last_run = tool.utc_now()
                    LOG.info(f'Task: {task.function.__name__} finished')
        time.sleep(60)


if 'gunicorn' in sys.modules:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.basicConfig(level=gunicorn_logger.level, handlers=gunicorn_logger.handlers)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    tool.execute(run_scheduled_tasks)


@app.route("/schedule/", methods=['GET', 'POST'])
def schedule_endpoint():
    if request.method == 'POST':
        LOG.info(f'Scheduling function {maintain_task.__name__}')
        soon = tool.utc_now() + timedelta(seconds=1)
        task = tool.Clazz(next_run=soon, last_run=None, running=False, function=maintain_task)
        TASKS.append(task)

    LOG.info('Listing threads')
    threads = [
        {
            'name': thread.name,
            'daemon': thread.daemon,
            'alive': thread.is_alive()
        }
        for thread in threading.enumerate()
    ]

    def default(obj):
        if callable(obj):
            return obj.__name__

    return json.dumps(dict(threads=threads, tasks=TASKS), option=json.OPT_INDENT_2, default=default).decode('utf-8')


def run_module(debug: bool):
    tool.execute(run_scheduled_tasks)
    return app.run(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_module(debug=debug)


if __name__ == "__main__":
    main()
