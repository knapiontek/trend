from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pprint import pprint
from typing import Dict, List, Any

import orjson as json
import pandas as pd
import xlrd

from src import exante, config, tool
from src.clazz import Clazz

EXANTE_TRANSACTIONS = 'exante_transactions'
COMMISSIONS = 'commissions'
DIVIDENDS = 'dividend'
TRADE = 'trade'


class Currency(Enum):
    PLN = auto()
    EUR = auto()
    USD = auto()


class CurrencyExchange:
    def __init__(self):
        self.nbp = read_nbp()

    def convert(self, dt: datetime, currency: Currency) -> float:
        assert dt.year == 2020
        dt -= timedelta(days=1)
        while dt not in self.nbp:
            dt -= timedelta(days=1)
            assert dt.year == 2020
        return self.nbp[dt][currency]


def read_nbp() -> Dict[datetime, Clazz]:
    xls = config.EXANTE_PATH.joinpath('nbp_2020.xls')
    workbook = xlrd.open_workbook(xls)
    sheet = workbook.sheet_by_name('Kursy średnie')
    return {
        xlrd.xldate_as_datetime(sheet.cell(i, 0).value, 0): Clazz(USD=sheet.cell(i, 2).value,
                                                                  EUR=sheet.cell(i, 8).value)
        for i in range(2, sheet.nrows - 4)
    }


def read_json(filename: str):
    path = config.STORE_PATH.joinpath(filename).with_suffix('.json')
    with path.open() as read_io:
        return [Clazz(**dt) for dt in json.loads(read_io.read())]


def write_json(filename: str, content: List[Dict[str, Any]]):
    path = config.STORE_PATH.joinpath(filename).with_suffix('.json')
    with path.open('wb') as write_io:
        write_io.write(json.dumps(content, option=json.OPT_INDENT_2, default=tool.json_default))


def write_csv(filename: str, content: List[Clazz]):
    df = pd.DataFrame(content)
    path = config.STORE_PATH.joinpath(filename).with_suffix('.csv')
    df.to_csv(path, index=False, header=True)


def save_exante_transactions():
    with exante.Session() as session:
        transactions = session.transactions()
        write_json(EXANTE_TRANSACTIONS, transactions)


def analyse_exante_transactions():
    transactions = read_json(EXANTE_TRANSACTIONS)

    write_json(COMMISSIONS, [t for t in transactions if t.type in ('COMMISSION', 'INTEREST')])
    write_json(DIVIDENDS, [t for t in transactions if t.type in ('TAX', 'DIVIDEND')])

    trades = [t for t in transactions if t.type == 'TRADE']

    open_transactions = defaultdict(Clazz)
    for tr in transactions:
        t = Clazz(**tr)
        if t.type == 'TRADE':
            if t.symbol == 'KRU.WSE':
                pprint(t)
            if t.asset == t.symbol:
                open_transactions[t.timestamp].update({'quantity': t.sum})
            else:
                open_transactions[t.timestamp].update(t)

    pprint(open_transactions)


if __name__ == '__main__':
    exchange = CurrencyExchange()
    assert 4.5084 == exchange.convert(datetime(2020, 12, 27), Currency.EUR)
