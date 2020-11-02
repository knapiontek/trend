import logging
import time
from datetime import datetime
from typing import List, Tuple, Dict, Any

import orjson as json
from arango import ArangoClient, ArangoServerError
from arango.database import StandardDatabase

from src import config, tool

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
            'health-exante': {'type': 'boolean'},
            'health-yahoo': {'type': 'boolean'},
            'health-stooq': {'type': 'boolean'},
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
                     'health-exante',
                     'health-yahoo',
                     'health-stooq',
                     'total']
    }
}

SECURITY_SCHEMA = {
    'message': 'security-schema',
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
            'volume': {'type': 'integer'},
            'sma': {'type': ['number', 'null'], 'format': 'float'},
            'vma': {'type': ['number', 'null'], 'format': 'float'},
            'order': {'type': ['integer', 'null']}
        },
        'required': ['symbol', 'timestamp', 'open', 'close', 'low', 'high', 'volume', 'sma', 'vma', 'order']
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


def create_collection(db: StandardDatabase, name: str, unique_fields: Tuple, schema: Dict):
    if not db.has_collection(name):
        collection = db.create_collection(name=name, schema=schema)
        collection.add_hash_index(fields=unique_fields, unique=True)


class Series:
    def __init__(self, name: str, editable: bool, unique_fields: Tuple, schema: Dict):
        time.sleep(0.2)
        self.name = name
        self.editable = editable
        self.db = db_connect()
        create_collection(self.db, self.name, unique_fields, schema)

    def __enter__(self):
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

    def __iadd__(self, series: List[tool.Clazz]) -> 'Series':
        result = self.tnx_collection.insert_many(series)
        return self.verify_result(result)

    def __ior__(self, series: List[tool.Clazz]) -> 'Series':
        result = self.tnx_collection.update_many(series)
        return self.verify_result(result)

    def verify_result(self, result: List) -> 'Series':
        errors = [str(e) for e in result if isinstance(e, ArangoServerError)]
        if len(errors):
            error = json.dumps(errors, option=json.OPT_INDENT_2).decode('utf')
            LOG.exception(error)
            raise Exception(error)
        return self


class ExchangeSeries(Series):
    def __init__(self, editable=False):
        super().__init__('exchange', editable, ('exchange', 'short-symbol'), EXCHANGE_SCHEMA)

    def __getitem__(self, exchange: str) -> List[tool.Clazz]:
        query = '''
            FOR datum IN @@collection
                FILTER datum.exchange == @exchange
                RETURN datum
        '''
        records = self.tnx_db.aql.execute(query, bind_vars={'exchange': exchange, '@collection': self.name})
        return [tool.Clazz(**r) for r in records]


class SecuritySeries(Series):
    def __init__(self, name: str, editable: bool, dt_from: datetime, order: bool):
        super().__init__(name, editable, ('symbol', 'timestamp'), SECURITY_SCHEMA)
        self.ts_from = tool.to_timestamp(dt_from)
        self.order = order

    def __getitem__(self, symbol: str) -> List[tool.Clazz]:
        query = '''
            FOR datum IN @@collection
                SORT datum.timestamp
                FILTER datum.symbol == @symbol and datum.timestamp >= @timestamp and datum.order >= @order
                RETURN datum
        '''
        bind_vars = {'symbol': symbol, '@collection': self.name, 'timestamp': self.ts_from, 'order': self.order}
        records = self.tnx_db.aql.execute(query, bind_vars=bind_vars)
        return [tool.Clazz(**r) for r in records]

    def time_range(self) -> List[tool.Clazz]:
        query = '''
            FOR datum IN @@collection
                COLLECT symbol = datum.symbol
                AGGREGATE min_ts = MIN(datum.timestamp), max_ts = MAX(datum.timestamp)
                RETURN {symbol, min_ts, max_ts}
        '''
        records = self.tnx_db.aql.execute(query, bind_vars={'@collection': self.name})
        return [tool.Clazz(**r) for r in records]


def exchange_clean():
    LOG.info(f'>> {exchange_clean.__name__}')

    db = db_connect()
    names = [c['name'] for c in db.collections()]
    for name in names:
        if name.startswith('exchange'):
            LOG.debug(f'Cleaning arango collection: {name}')
            deleted = db.delete_collection(name)
            assert deleted


def security_clean(engine: Any):
    engine_name = tool.module_name(engine.__name__)
    LOG.info(f'>> {security_clean.__name__}({engine_name})')

    db = db_connect()
    names = [c['name'] for c in db.collections()]
    for name in names:
        if name.startswith(f'security_{tool.module_name(engine.__name__)}'):
            LOG.debug(f'Cleaning arango collection: {name}')
            deleted = db.delete_collection(name)
            assert deleted
