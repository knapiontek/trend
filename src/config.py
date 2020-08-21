import json
import pathlib
from datetime import timezone, timedelta
from functools import lru_cache
from typing import Tuple

import jsonschema

from src import config_schema

UTC_TZ = timezone(timedelta(hours=0), 'GMT')
DUBLIN_TZ = timezone(timedelta(hours=1), 'GMT')

DURATION_1M = 60
DURATION_5M = 5 * 60
DURATION_10M = 10 * 60
DURATION_15M = 15 * 60
DURATION_1H = 60 * 60
DURATION_6H = 6 * 60 * 60
DURATION_1D = 24 * 60 * 60

TREND_PATH = pathlib.Path(__file__).parent.parent
STORE_PATH = TREND_PATH.joinpath('store')
LOG_PATH = TREND_PATH.joinpath('logs')
CONFIG_FILE = pathlib.Path('~/.trend').expanduser()
LOG_FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'


def duration_name(duration: int) -> str:
    return {
        DURATION_1M: '1m',
        DURATION_5M: '5m',
        DURATION_10M: '10m',
        DURATION_15M: '15m',
        DURATION_1H: '1h',
        DURATION_6H: '6h',
        DURATION_1D: '1d'
    }[duration]


def duration_delta(duration: int) -> timedelta:
    return timedelta(seconds=duration)


@lru_cache(maxsize=1)
def load_file():
    with CONFIG_FILE.open() as read_io:
        config = json.load(read_io)
        jsonschema.validate(config, config_schema.CONFIG_SCHEMA)
        return config


def exante_url() -> str:
    config = load_file()
    exante_config = config['exante']
    return exante_config['data-url']


def exante_auth() -> Tuple[str, str]:
    config = load_file()
    exante_config = config['exante']
    return exante_config['app'], exante_config['shared-key']


def notify_channel() -> str:
    config = load_file()
    return config['notify-run']['channel']


def quandl_auth() -> str:
    config = load_file()
    return config['quandl']['shared-key']


def iex_auth() -> str:
    config = load_file()
    return config['iex']['shared-key']


def arango_db_auth() -> Tuple[str, str, str, str]:
    config = load_file()
    arango_config = config['arango-db']
    return arango_config['url'], arango_config['username'], arango_config['password'], arango_config['database']
