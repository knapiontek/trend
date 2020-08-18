import logging
import pathlib
import sys
from logging.handlers import RotatingFileHandler
from pprint import pprint

from src import config


def init(script_file: str, persist=False):
    handlers = [logging.StreamHandler(sys.stdout)]
    if persist:
        stem = pathlib.Path(script_file).stem
        file_name = config.LOG_PATH.joinpath(f'{stem}.log')
        pprint(f'logging to file: {file_name}')
        file_handler = RotatingFileHandler(file_name,
                                           maxBytes=2e6,
                                           backupCount=5)
        handlers.append(file_handler)
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.basicConfig(level=logging.DEBUG, format=config.LOG_FORMAT, handlers=handlers)
