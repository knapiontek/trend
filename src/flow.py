import atexit
import logging
import sys
import threading
from typing import Union, Sized

from src import config

LOG = logging.getLogger(__name__)

EXIT_EVENT = threading.Event()


def wait(timeout: float) -> bool:
    """:returns True except shutdown has been triggered"""
    is_set = EXIT_EVENT.wait(timeout)
    if is_set:
        raise KeyboardInterrupt()
    return True


@atexit.register
def shutdown():
    LOG.info('Shutting down the system')
    EXIT_EVENT.set()


SPACES = ' ' * 43


class Progress:
    def __init__(self, title: str, size: Union[int, Sized]):
        self.count = 0
        self.title = title
        self.length = len(size) if isinstance(size, Sized) else size
        self.last_message = None

    def __enter__(self) -> 'Progress':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            if self.last_message:
                LOG.warning(self.last_message)
        else:
            if self.length:
                self.print(f'{self.title}: {100 * self.count / self.length:.1f}% done{SPACES}\n')
                assert self.count == self.length
            else:
                self.print(f'{self.title}: done{SPACES}\n')

    def __call__(self, message: str):
        self.print(f'{self.title}: {100 * self.count / self.length:.1f}% {message}{SPACES}\r')
        self.count += 1
        wait(config.loop_delay())

    def print(self, message: str):
        sys.stdout.write(message)
        sys.stdout.flush()
        self.last_message = message
