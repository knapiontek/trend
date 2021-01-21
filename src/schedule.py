import logging
import sys
import threading
from datetime import timedelta

import orjson as json
from flask import Flask, request

from src import data, log, yahoo, exante, stooq, config, tool, flow
from src.clazz import Clazz
from src.tool import DateTime

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


TASKS = [
    Clazz(interval=tool.INTERVAL_1D,
          hour=2,
          minute=30,
          next_run=None,
          last_run=None,
          running=False,
          function=maintain_task)
]


def run_scheduled_tasks():
    for task in TASKS:
        utc_now = DateTime.now()
        task.next_run = utc_now.replace(hour=task.hour, minute=task.minute, second=0, microsecond=0)
        if task.next_run < utc_now:
            task.next_run += task.interval

    while flow.wait(60.0):
        for task in TASKS:
            if task.next_run < DateTime.now():
                try:
                    LOG.info(f'Task: {task.function.__name__} has started')
                    task.running = True
                    task.function()
                except:
                    pass
                finally:
                    LOG.info(f'Task: {task.function.__name__} has finished')
                    if 'interval' in task:
                        task.next_run += task.interval
                        task.last_run = DateTime.now()
                        task.running = False
                    else:
                        TASKS.remove(task)


if 'gunicorn' in sys.modules:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.basicConfig(level=gunicorn_logger.level, handlers=gunicorn_logger.handlers)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    flow.execute(run_scheduled_tasks)


@app.route("/schedule/", methods=['GET', 'POST'])
def schedule_endpoint():
    if request.method == 'POST':
        LOG.info(f'Scheduling function {maintain_task.__name__}')
        task = Clazz(next_run=DateTime.now().replace(microsecond=0), running=False, function=maintain_task)
        TASKS.append(task)

    LOG.info('Listing threads and tasks')
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
        elif isinstance(obj, timedelta):
            return str(obj)

    return json.dumps(dict(threads=threads, tasks=TASKS), option=json.OPT_INDENT_2, default=default).decode('utf-8')


def run_module(debug: bool):
    flow.execute(run_scheduled_tasks)
    return app.run(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_module(debug=debug)


if __name__ == "__main__":
    main()
