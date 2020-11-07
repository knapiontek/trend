import sys
import time
from typing import Union, Sized

from src import config

SPACES = ' ' * 43


def print_line(message: str):
    sys.stdout.write(message)
    sys.stdout.flush()


class Progress:
    def __init__(self, title: str, size: Union[int, Sized]):
        self.count = -1
        self.title = title
        self.length = len(size) if isinstance(size, Sized) else size

    def __enter__(self) -> 'Progress':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            if self.length:
                self.count += 1
                print_line(f'{self.title}: {100 * self.count / self.length:.1f}% done{SPACES}\n')
                assert self.count == self.length
            else:
                print_line(f'{self.title}: done{SPACES}\n')

    def __call__(self, message: str):
        self.count += 1
        print_line(f'{self.title}: {100 * self.count / self.length:.1f}% {message}{SPACES}\r')
        time.sleep(config.loop_delay())
