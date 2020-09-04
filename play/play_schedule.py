import asyncio
import logging
import sys
from asyncio import CancelledError
from datetime import datetime, timedelta
from types import coroutine

from aiohttp import web

from src import tools

LOG = logging.getLogger(__name__)

RUNNING = True  # False on_cleanup


async def sleep_until(dt: datetime):
    # sleep until the specified datetime
    while dt > tools.utc_now():
        remaining = (dt - tools.utc_now()).total_seconds()
        await asyncio.sleep(remaining % (24 * 60 * 60))
        LOG.debug(f'{sleep_until.__name__} waken-up after {remaining} seconds')


BACKGROUND_TASK_GUARD = asyncio.Lock()


async def shield_coro(coro: coroutine, *args, **kwargs):
    try:
        async with BACKGROUND_TASK_GUARD:
            return await asyncio.shield(coro(*args, **kwargs))
    except CancelledError:
        pass
    except Exception as exc:
        LOG.exception(exc)


async def run_at(dt: datetime, coro: coroutine, *args, **kwargs):
    await sleep_until(dt)
    return await shield_coro(coro, *args, **kwargs)


async def run_daily_at(dt: datetime, coro: coroutine, *args, **kwargs):
    await sleep_until(dt)
    await shield_coro(coro, *args, **kwargs)
    while RUNNING:
        dt += timedelta(days=1)
        await sleep_until(dt)
        await shield_coro(coro, *args, **kwargs)


async def run_every(seconds: int, coro: coroutine, *args, **kwargs):
    while RUNNING:
        await asyncio.sleep(seconds)
        await shield_coro(coro, *args, **kwargs)


def task_example():
    pass


def schedule_topo_refresh_daily():
    dt = tools.utc_now()
    dt = dt.replace(hour=22, minute=13, second=0, microsecond=0)
    asyncio.create_task(run_daily_at(dt, task_example))


async def launch(app: web.Application) -> None:
    schedule_topo_refresh_daily()


async def shutdown(app: web.Application) -> None:
    LOG.info("shutting down scheduled tasks ...")
    schedule_module = sys.modules[__name__]
    schedule_module.RUNNING = False

    for i in range(10):
        running_coros = {task._coro.__name__ for task in asyncio.Task.all_tasks() if not task.done()}
        if running_coros == {'_run_app'}:
            return
        LOG.info(f"waiting for running tasks {running_coros - {'_run_app'}}")
        await asyncio.sleep(3)
