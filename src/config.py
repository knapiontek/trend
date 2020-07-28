import json
import pathlib

TREND_FOLDER = pathlib.Path(__file__).parent.parent
STORE_FOLDER = TREND_FOLDER.joinpath('store')
CONFIG_FILE = pathlib.Path('~/.trend').expanduser()


def load():
    with CONFIG_FILE.open() as read_io:
        return json.load(read_io)


def exante():
    config = load()
    exante_config = config['exante']
    return exante_config['app'], exante_config['shared-key']
