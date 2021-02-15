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
DIVIDENDS = 'dividends'
TRADES = 'trades'


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


def split_transactions():
    transactions = read_json(EXANTE_TRANSACTIONS)

    commissions = [t for t in transactions if t.type in ('COMMISSION', 'INTEREST')]
    write_json(COMMISSIONS, commissions)
    write_csv(COMMISSIONS, commissions)

    dividends = [t for t in transactions if t.type in ('TAX', 'DIVIDEND')]
    write_json(DIVIDENDS, dividends)
    write_csv(DIVIDENDS, dividends)

    trades = [t for t in transactions if t.type == 'TRADE']
    write_json(TRADES, trades)
    write_csv(TRADES, trades)


def to_datetime(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp // 1000).isoformat(sep=' ')


def sort_trades() -> Dict:
    trades = read_json(TRADES)

    symbol_transactions = defaultdict(list)
    for t in trades:
        symbol_transactions[t.symbol] += [t]

    symbol_trades = {}
    for symbol, trades in symbol_transactions.items():
        trade_index = defaultdict(list)
        for t in trades:
            trade_index[to_datetime(t.timestamp)] += [Clazz(asset=t.asset, sum=float(t.sum))]
        symbol_trades[symbol] = trade_index

    return {k: dict(v) for k, v in symbol_trades.items()}


def calculate():
    trades = sort_trades()
    for symbol, time_transactions in trades.items():

        pprint(time_transactions, width=200)
        pending = []

        for dt, sub_transactions in time_transactions.items():

            time_transaction = Clazz()
            for t in sub_transactions:
                if symbol == t.asset:
                    time_transaction.side = 'long' if t.sum > 0 else 'short'
                    time_transaction.quantity = abs(t.sum)
                else:
                    time_transaction.value = abs(t.sum)
                    time_transaction.currency = t.asset
            time_transaction.unit = round(time_transaction.value / time_transaction.quantity, 6)
            pprint(time_transaction, width=1000)

            for p in pending:
                if time_transaction.quantity != 0.0 and p.side != time_transaction.side:
                    if p.quantity <= time_transaction.quantity:
                        time_transaction.quantity -= p.quantity
                        p.quantity = 0.0
                        pprint(f'reduction old p: {p.quantity} t: {time_transaction.quantity}')
                    elif p.quantity > time_transaction.quantity:
                        p.quantity -= time_transaction.quantity
                        time_transaction.quantity -= 0.0
                        pprint(f'reduction new p: {p.quantity} t: {time_transaction.quantity}')

            pending = [p for p in pending if p.quantity != 0]
            if time_transaction.quantity != 0.0:
                pending += [time_transaction]
        break


if __name__ == '__main__':
    # save_exante_transactions()
    split_transactions()

    exchange = CurrencyExchange()
    assert 3.6981 == exchange.value(datetime(2020, 12, 27), Currency.USD)

    calculate()
