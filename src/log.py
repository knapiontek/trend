import logging
import pathlib
import sys
from logging.handlers import RotatingFileHandler

from src import config


def init(script_file: str, debug: bool, to_screen=False, to_file=False):
    handlers = []
    if to_screen:
        handlers.append(logging.StreamHandler(sys.stdout))
    if to_file:
        stem = pathlib.Path(script_file).stem
        file_name = config.LOG_PATH.joinpath(f'{stem}.log')
        print(f'logging to file: {file_name}')
        file_handler = RotatingFileHandler(file_name, maxBytes=2e6, backupCount=5)
        handlers.append(file_handler)
    level = [logging.INFO, logging.DEBUG][debug]
    logging.basicConfig(level=level, format=config.LOG_FORMAT, handlers=handlers)
    logging.getLogger('urllib3').setLevel(logging.INFO)
