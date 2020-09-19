import logging
from typing import List, Tuple, Iterable, Dict, Any

import orjson as json
from arango import ArangoClient, DocumentInsertError
from arango.database import StandardDatabase

from src import config, tools

LOG = logging.getLogger(__name__)


class FileStore(dict):
    def __init__(self, name: str, editable=False):
        super().__init__()
        self.editable = editable
        self.filename = config.STORE_PATH.joinpath(f'{name}.json')

    def __enter__(self) -> 'FileStore':
        if self.filename.exists():
            with self.filename.open() as read_io:
                self.update(json.loads(read_io.read()))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.editable and not exc_type:
            with self.filename.open('wb') as write_io:
                write_io.write(json.dumps(self, option=json.OPT_INDENT_2))

    def __setitem__(self, key: str, value: Any):
        assert self.editable
        super().__setitem__(key, value)

    def tuple_it(self, keys: Iterable[str]) -> Iterable[Tuple]:
        return tools.tuple_it(self, keys)

    def dict_it(self, keys: Iterable[str]) -> Iterable[Dict]:
        return tools.dict_it(self, keys)

    def loop_it(self, key: str) -> Iterable[Any]:
        return tools.loop_it(self, key)


SERIES_SCHEMA = {
    'message': 'series-schema',
    'level': 'strict',
    'rule': {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'symbol': {'type': 'string'},
            'timestamp': {'type': 'integer'},
            'open': {'type': 'number', 'format': 'float'},
            'close': {'type': 'number', 'format': 'float'},
            'low': {'type': 'number', 'format': 'float'},
            'high': {'type': 'number', 'format': 'float'},
            'volume': {'type': 'integer'}
        },
        'required': ['symbol', 'timestamp', 'open', 'close', 'low', 'high', 'volume']
    }
}

EXCHANGE_SCHEMA = {
    'message': 'exchange-schema',
    'level': 'strict',
    'rule': {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'symbol': {'type': 'string'},
            'type': {'type': 'string'},
            'exchange': {'type': 'string'},
            'currency': {'type': 'string'},
            'name': {'type': 'string'},
            'description': {'type': 'string'},
            'short-symbol': {'type': 'string'},
            'shortable': {'type': 'boolean'},
            'health': {'type': 'boolean'},
            'total': {'type': 'number', 'format': 'float'}

        },
        'required': ['symbol',
                     'type',
                     'exchange',
                     'currency',
                     'name',
                     'description',
                     'short-symbol',
                     'shortable',
                     'health',
                     'total']
    }
}


def db_connect() -> StandardDatabase:
    url, username, password, db_name = config.arango_db_auth()
    client = ArangoClient(hosts=url)
    sys_db = client.db('_system', username=username, password=password)
    if not sys_db.has_database(db_name):
        sys_db.create_database(db_name)
    db = client.db(db_name, username=username, password=password)
    return db


def create_collection(db: StandardDatabase, name: str, unique_fields: Tuple):
    if not db.has_collection(name):
        collection = db.create_collection(name)
        collection.add_hash_index(fields=unique_fields, unique=True)


class Series:
    def __init__(self, name: str, editable: bool, unique_fields: Tuple):
        self.name = name
        self.editable = editable
        self.db = db_connect()
        create_collection(self.db, self.name, unique_fields)

    def __enter__(self) -> 'Series':
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

    def handle_insert_result(self, result: List) -> 'Series':
        errors = [str(e) for e in result if isinstance(e, DocumentInsertError)]
        if len(errors):
            error = json.dumps(errors, option=json.OPT_INDENT_2).decode('utf')
            LOG.exception(error)
            raise Exception(error)
        return self


class TimeSeries(Series):
    def __init__(self, name: str, editable: bool):
        super().__init__(name, editable, ('symbol', 'timestamp'))

    def __add__(self, series: List[Dict]):
        result = self.tnx_collection.insert_many(series)
        return self.handle_insert_result(result)

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


class Exchange(Series):
    def __init__(self, editable=False):
        super().__init__('exchange', editable, ('exchange', 'short-symbol'))

    def __setitem__(self, exchange: str, series: List[Dict]):
        removed = self.tnx_collection.delete_match({'exchange': exchange})
        LOG.info(f'Removed {removed} items from {exchange}')
        result = self.tnx_collection.insert_many(series)
        return self.handle_insert_result(result)

    def __getitem__(self, exchange: str) -> List[Dict]:
        query = '''
            FOR series IN @@collection
                FILTER series.exchange == @exchange
                RETURN series
        '''
        result = self.tnx_db.aql.execute(query, bind_vars={'exchange': exchange, '@collection': self.name})
        return list(result)


def series_empty():
    LOG.info(f'>> {series_empty.__name__}')

    db = db_connect()
    names = [c['name'] for c in db.collections()]
    for name in names:
        if name.startswith('series'):
            LOG.info(f'Emptying series: {name}')
            collection = db.collection(name)
            collection.delete_match({})


def exchange_empty():
    LOG.info(f'>> {exchange_empty.__name__}')

    db = db_connect()
    names = [c['name'] for c in db.collections()]
    for name in names:
        if name.startswith('exchange'):
            LOG.info(f'Emptying exchange: {name}')
            collection = db.collection(name)
            for exchange in config.ACTIVE_EXCHANGES:
                removed = collection.delete_match({'exchange': exchange})
                LOG.info(f'Removed {removed} items from {exchange}')
