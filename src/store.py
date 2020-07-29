import json
from typing import Dict

from src import config


class Store:
    def __init__(self, name: str):
        self.filename = config.STORE_FOLDER.joinpath(f'{name}.json')
        self.content = {}

    def __enter__(self) -> Dict:
        if self.filename.exists():
            with self.filename.open() as read_io:
                self.content = json.load(read_io)
        return self.content

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            with self.filename.open('w') as write_io:
                json.dump(self.content, write_io, indent=2)
