import json
import pathlib
from functools import lru_cache

import jsonschema

from src import config_schema

TREND_FOLDER = pathlib.Path(__file__).parent.parent
STORE_FOLDER = TREND_FOLDER.joinpath('store')
CONFIG_FILE = pathlib.Path('~/.trend').expanduser()


@lru_cache(maxsize=None)
def load():
    with CONFIG_FILE.open() as read_io:
        config = json.load(read_io)
        jsonschema.validate(config, config_schema.CONFIG_SCHEMA)
        return config


def exante_url():
    config = load()
    exante_config = config['exante']
    return exante_config['data-url']


def exante_auth():
    config = load()
    exante_config = config['exante']
    return exante_config['app'], exante_config['shared-key']


def notify_channel():
    config = load()
    return config['notify-run']['channel']


def quandl_auth():
    config = load()
    quandl_config = config['quandl']
    return quandl_config['shared-key']


def iex_auth():
    config = load()
    iex_config = config['iex']
    return iex_config['shared-key']
