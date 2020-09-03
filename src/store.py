import json
import logging
from functools import lru_cache
from typing import List, Tuple, Iterable, Dict, Any

from arango import ArangoClient, DocumentInsertError
from arango.database import StandardDatabase

from src import config, tools

LOG = logging.getLogger(__name__)


class FileStore(dict):
    def __init__(self, name: str, editable=False):
        super(FileStore, self).__init__()
        self.editable = editable
        self.filename = config.STORE_PATH.joinpath(f'{name}.json')

    def __enter__(self) -> 'FileStore':
        if self.filename.exists():
            with self.filename.open() as read_io:
                self.update(json.load(read_io))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.editable and not exc_type:
            with self.filename.open('w') as write_io:
                json.dump(self, write_io, indent=2)

    def __setitem__(self, key: str, value: Any):
        assert self.editable
        super(FileStore, self).__setitem__(key, value)

    def tuple_it(self, keys: Iterable[str]) -> Iterable[Tuple]:
        return tools.tuple_it(self, keys)

    def dict_it(self, keys: Iterable[str]) -> Iterable[Dict]:
        return tools.dict_it(self, keys)


CANDLE_SCHEMA = {
    'message': 'candle-schema',
    'level': 'strict',
    'rule': {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'symbol': {'type': 'string'},
            'timestamp': {'type': 'integer'},
            'open': {'type': 'string'},
            'close': {'type': 'string'},
            'low': {'type': 'string'},
            'high': {'type': 'string'},
            'volume': {'type': 'string', 'format': 'integer'}
        },
        'required': ['symbol', 'timestamp', 'open', 'close', 'low', 'high', 'volume']
    }
}


@lru_cache(maxsize=1)
def db_connect() -> StandardDatabase:
    url, username, password, db_name = config.arango_db_auth()
    client = ArangoClient(hosts=url)
    sys_db = client.db('_system', username=username, password=password)
    if not sys_db.has_database(db_name):
        sys_db.create_database(db_name)
    db = client.db(db_name, username=username, password=password)
    return db


def create_collection(db: StandardDatabase, name: str):
    if not db.has_collection(name):
        collection = db.create_collection(name)
        collection.add_hash_index(fields=['symbol', 'timestamp'], unique=True)


class DBSeries:
    def __init__(self, name: str, editable=False):
        self.name = name
        self.editable = editable
        self.db = db_connect()
        create_collection(self.db, self.name)

    def __enter__(self) -> 'DBSeries':
        write = self.name if self.editable else None
        self.tnx_db = self.db.begin_transaction(read=self.name, write=write)
        self.tnx_collection = self.tnx_db.collection(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.editable and self.tnx_db:
            if exc_type:
                self.tnx_db.abort_transaction()
            else:
                self.tnx_db.commit_transaction()

    def __add__(self, series: List[Dict]):
        result = self.tnx_collection.insert_many(series)
        errors = [str(e) for e in result if isinstance(e, DocumentInsertError)]
        if len(errors):
            error = json.dumps(errors, indent=2)
            LOG.exception(error)
            raise Exception(error)
        return self

    def __getitem__(self, symbol: str) -> List[Dict]:
        query = '''
            FOR series IN @@collection
                FILTER series.symbol == @symbol
                RETURN series
        '''
        result = self.tnx_db.aql.execute(query, bind_vars={'symbol': symbol, '@collection': self.name})
        return list(result)

    def time_range(self) -> List[Dict]:
        query = '''
            FOR series IN @@collection
                COLLECT symbol = series.symbol
                AGGREGATE min_ts = MIN(series.timestamp), max_ts = MAX(series.timestamp)
                RETURN {symbol, min_ts, max_ts}
        '''
        result = self.tnx_db.aql.execute(query, bind_vars={'@collection': self.name})
        return list(result)


def empty_series():
    db = db_connect()
    names = [c['name'] for c in db.collections()]
    for name in names:
        if name.startswith('series'):
            collection = db.collection(name)
            collection.delete_match({})
