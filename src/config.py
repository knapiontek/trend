import json
import pathlib
from functools import lru_cache

import jsonschema

from src import config_schema

TREND_PATH = pathlib.Path(__file__).parent.parent
STORE_PATH = TREND_PATH.joinpath('store')
LOG_PATH = TREND_PATH.joinpath('logs')
CONFIG_FILE = pathlib.Path('~/.trend').expanduser()
LOG_FORMAT = '%(asctime)s %(levelname)s %(module)s %(message)s'


@lru_cache(maxsize=None)
def load_file():
    with CONFIG_FILE.open() as read_io:
        config = json.load(read_io)
        jsonschema.validate(config, config_schema.CONFIG_SCHEMA)
        return config


def exante_url():
    config = load_file()
    exante_config = config['exante']
    return exante_config['data-url']


def exante_auth():
    config = load_file()
    exante_config = config['exante']
    return exante_config['app'], exante_config['shared-key']


def notify_channel():
    config = load_file()
    return config['notify-run']['channel']


def quandl_auth():
    config = load_file()
    return config['quandl']['shared-key']


def iex_auth():
    config = load_file()
    return config['iex']['shared-key']
