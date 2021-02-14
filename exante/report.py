import math
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
        self.nbp = {}
        self.nbp.update(read_nbp(2020))
        self.nbp.update(read_nbp(2021))

    def value(self, dt: datetime, currency: Currency) -> float:
        assert dt.year == 2020
        dt -= timedelta(days=1)
        while dt not in self.nbp:
            dt -= timedelta(days=1)
            assert dt.year == 2020
        return self.nbp[dt][currency.name]


def read_nbp(year) -> Dict[datetime, Clazz]:
    xls = config.EXANTE_PATH.joinpath(f'nbp_{year}.xls')
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
    df = pd.DataFrame([c.to_dict() for c in content])
    path = config.STORE_PATH.joinpath(filename).with_suffix('.csv')
    df.to_csv(path, index=False, header=True)


def save_exante_transactions():
    with exante.Session() as session:
        transactions = session.transactions()
        write_json(EXANTE_TRANSACTIONS, transactions)
        write_csv(EXANTE_TRANSACTIONS, transactions)


def analyse_exante_transactions():
    transactions = read_json(EXANTE_TRANSACTIONS)

    write_json(COMMISSIONS, [t for t in transactions if t.type in ('COMMISSION', 'INTEREST')])
    write_json(DIVIDENDS, [t for t in transactions if t.type in ('TAX', 'DIVIDEND')])

    trades = [t for t in transactions if t.type == 'TRADE']

    trade_index = defaultdict(lambda: Clazz(quantity=0.0, price=0.0, currency=None))
    for t in trades:
        i = trade_index[t.timestamp]
        i.datetime = datetime.fromtimestamp(t.timestamp // 1000).isoformat(sep=' ')
        if t.symbol.endswith('.EXANTE'):
            i.symbol = t.symbol  # currency exchange, no need for 2020
        else:
            if t.asset == t.symbol:
                i.symbol = t.symbol
                i.quantity += float(t.sum)
            else:
                i.price += float(t.sum)
                assert not i.currency or i.currency == t.asset
                i.currency = t.asset

    trades = sorted(trade_index.values(), key=lambda x: x.datetime)
    for t in trades:
        if math.copysign(1.0, t.quantity) != -math.copysign(1.0, t.price):
            pprint(t)


if __name__ == '__main__':
    # save_exante_transactions()

    exchange = CurrencyExchange()
    assert 3.6981 == exchange.value(datetime(2020, 12, 27), Currency.USD)

    analyse_exante_transactions()
