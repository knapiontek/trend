import json
from functools import lru_cache
from typing import List, Dict

from arango import ArangoClient
from arango.collection import StandardCollection
from arango.database import StandardDatabase

from src import config


class FileStore:
    def __init__(self, name: str):
        self.filename = config.STORE_PATH.joinpath(f'{name}.json')
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


@lru_cache(maxsize=1)
def db_connect() -> StandardDatabase:
    url, username, password, db_name = config.arango_db_auth()
    client = ArangoClient(hosts=url)
    sys_db = client.db('_system', username=username, password=password)
    if not sys_db.has_database(db_name):
        sys_db.create_database(db_name)
    db = client.db(db_name, username=username, password=password)
    return db


def db_collection(db: StandardDatabase, name: str) -> StandardCollection:
    if db.has_collection(name):
        collection = db.collection(name)
    else:
        collection = db.create_collection(name)
    return collection


class DBSeries:
    def __init__(self, duration: int):
        duration_name = config.duration_name(duration)
        self.db = db_connect()
        self.collection = db_collection(self.db, f'series_{duration_name}')

    def __enter__(self) -> 'DBSeries':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            pass

    def __add__(self, series: List):
        self.collection.insert_many(series)
