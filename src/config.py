import pathlib
from functools import lru_cache
from typing import Tuple, Any

import jsonschema
import orjson as json

from src import config_schema

TREND_PATH = pathlib.Path(__file__).parent.parent
SRC_PATH = TREND_PATH.joinpath('src')
ASSETS_PATH = SRC_PATH.joinpath('assets')
STORE_PATH = TREND_PATH.joinpath('store')
EXANTE_PATH = TREND_PATH.joinpath('exante')
LOG_PATH = TREND_PATH.joinpath('logs')
CONFIG_FILE = pathlib.Path('~/.trend').expanduser()
LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'


@lru_cache(maxsize=1)
def load_file():
    with CONFIG_FILE.open() as read_io:
        config = json.loads(read_io.read())
        jsonschema.validate(config, config_schema.CONFIG_SCHEMA)
        return config


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


def arango_db_auth() -> Tuple[Any, ...]:
    config = load_file()
    arango_config = config['arango-db']
    return tuple(arango_config[key] for key in ('url', 'username', 'password', 'database'))
