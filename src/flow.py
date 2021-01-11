import atexit
import logging
import sys
import threading
from typing import Union, Sized

from src import config

LOG = logging.getLogger(__name__)

EXIT_EVENT = threading.Event()


def wait(timeout: float) -> bool:
    """:returns True except the shutdown has been triggered"""
    if EXIT_EVENT.wait(timeout):
        raise KeyboardInterrupt()
    return True


@atexit.register
def shutdown():
    LOG.info('Shutting down the system')
    EXIT_EVENT.set()


def execute(function):
    thread = threading.Thread(target=function, name=function.__name__)
    thread.daemon = True
    thread.start()


class Progress:
    def __init__(self, title: str, size: Union[int, Sized]):
        self.count = 0
        self.title = title
        self.length = len(size) if isinstance(size, Sized) else size
        self.last_message = ''

    def __enter__(self) -> 'Progress':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            if self.last_message:
                LOG.warning(self.last_message)
        else:
            if self.length:
                self.print(f'{self.title}: {100 * self.count / self.length:.1f}% done')
                assert self.count == self.length
            else:
                self.print(f'{self.title}: done')

    def __call__(self, message: str):
        self.print(f'{self.title}: {100 * self.count / self.length:.1f}% {message}', False)
        self.count += 1
        wait(config.loop_delay())

    def print(self, message: str, new_line=True):
        spaces = ''
        trail = ['\r', '\n'][new_line]
        len_message = len(message)
        len_last_message = len(self.last_message)
        if len_message > len_last_message:
            spaces = ' ' * (len_message - len_last_message)  # erase last message
        sys.stdout.write(f'{message}{spaces}{trail}')
        sys.stdout.flush()
        self.last_message = message
