import json
import logging
from functools import lru_cache
from typing import List, Dict

from arango import ArangoClient, DocumentInsertError
from arango.database import StandardDatabase

from src import config

LOG = logging.getLogger(__name__)


# there should be assert for editing if editable=False, changes is ignored now!

class FileStore:
    def __init__(self, name: str, editable=False):
        self.editable = editable
        self.filename = config.STORE_PATH.joinpath(f'{name}.json')
        self.content = {}

    def __enter__(self) -> Dict:
        if self.filename.exists():
            with self.filename.open() as read_io:
                self.content = json.load(read_io)
        return self.content

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type and self.editable:
            with self.filename.open('w') as write_io:
                json.dump(self.content, write_io, indent=2)


CANDLE_SCHEMA = {
    'message': 'candle-schema',
    'level': 'strict',
    'rule': {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'timestamp': {'type': 'integer'},
            'open': {'type': 'string'},
            'low': {'type': 'string'},
            'close': {'type': 'string'},
            'volume': {'type': 'string', 'format': 'integer'},
            'high': {'type': 'string'},
            'utc': {'type': 'string'},
            'dublin': {'type': 'string'},
            'symbol': {'type': 'string'}
        },
        'required': ['close', 'dublin', 'high', 'low', 'open', 'symbol', 'timestamp', 'utc', 'volume']
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
    def __init__(self, duration: int, editable=False):
        self.editable = editable
        duration_name = config.duration_name(duration)
        self.collection_name = f'series_{duration_name}'
        self.db = db_connect()
        create_collection(self.db, self.collection_name)

    def __enter__(self) -> 'DBSeries':
        write = self.collection_name if self.editable else None
        self.tnx_db = self.db.begin_transaction(read=self.collection_name, write=write)
        self.tnx_collection = self.tnx_db.collection(self.collection_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.editable and self.tnx_db:
            if exc_type:
                self.tnx_db.abort_transaction()
            else:
                self.tnx_db.commit_transaction()

    def __add__(self, series: List):
        result = self.tnx_collection.insert_many(series)
        errors = [str(e) for e in result if isinstance(e, DocumentInsertError)]
        if len(errors):
            error = json.dumps(errors, indent=2)
            LOG.exception(error)
            raise Exception(error)

    def __getitem__(self, symbol) -> List:
        query = '''
            FOR series IN series_1d
                FILTER series.symbol == @symbol
                RETURN series
        '''
        result = self.tnx_db.aql.execute(query, bind_vars={'symbol': symbol})
        return list(result)

    def time_range(self) -> List:
        query = '''
            FOR series IN series_1d
                COLLECT symbol = series.symbol
                AGGREGATE min_utc = MIN(series.utc), max_utc = MAX(series.utc)
                RETURN {symbol, min_utc, max_utc}
        '''
        result = self.tnx_db.aql.execute(query)
        return list(result)


def empty_series():
    db = db_connect()
    names = [c['name'] for c in db.collections()]
    for name in names:
        if name.startswith('series'):
            collection = db.collection(name)
            collection.delete_match({})
