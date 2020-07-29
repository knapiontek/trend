import json
import pathlib
from functools import lru_cache

TREND_FOLDER = pathlib.Path(__file__).parent.parent
STORE_FOLDER = TREND_FOLDER.joinpath('store')
CONFIG_FILE = pathlib.Path('~/.trend').expanduser()


@lru_cache(maxsize=None)
def load():
    with CONFIG_FILE.open() as read_io:
        return json.load(read_io)


def exante_url():
    config = load()
    exante_config = config['exante']
    return exante_config['url']


def exante_auth():
    config = load()
    exante_config = config['exante']
    return exante_config['app'], exante_config['shared-key']


def notify_channel():
    config = load()
    return config['notify-run']['channel']
