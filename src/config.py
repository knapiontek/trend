import pathlib
from datetime import datetime
from functools import lru_cache
from typing import Tuple

import jsonschema
import orjson as json

from src import schema
from src.tool import DateTime

TREND_PATH = pathlib.Path(__file__).parent.parent
SRC_PATH = TREND_PATH.joinpath('src')
TESTS_PATH = TREND_PATH.joinpath('tests')
ASSETS_PATH = SRC_PATH.joinpath('assets')
STORE_PATH = TREND_PATH.joinpath('store')
EXANTE_PATH = TREND_PATH.joinpath('exante')
LOG_PATH = TREND_PATH.joinpath('logs')
CONFIG_FILE = pathlib.Path('~/.trend').expanduser()
LOG_FORMAT = '[%(asctime)s] [%(levelname)s]\t[%(module)s]\t%(message)s'

EXCHANGES = ('WSE', 'XETRA', 'LSE', 'NASDAQ', 'NYSE')
HEALTH_MISSING_LIMIT = 20


@lru_cache(maxsize=1)
def load_file():
    with CONFIG_FILE.open() as read_io:
        config = json.loads(read_io.read())
        jsonschema.validate(config, schema.CONFIG_SCHEMA)
        return config


def loop_delay() -> float:
    config = load_file()
    return config['system']['loop-delay']


def datetime_from() -> datetime:
    config = load_file()
    return DateTime.parse_datetime(config['system']['date-time-from'])


def exante_account() -> str:
    config = load_file()
    exante_config = config['exante']
    return exante_config['account']


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
