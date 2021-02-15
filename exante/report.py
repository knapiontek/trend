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
TAX_TRANSACTIONS = 'tax_transactions'
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

    def value(self, time: str, currency: str) -> float:
        time = datetime.fromisoformat(time).replace(hour=0, minute=0, second=0)
        assert time.year == 2020
        time -= timedelta(days=1)
        while time not in self.nbp:
            time -= timedelta(days=1)
            assert time.year == 2020
        return self.nbp[time][currency]


def read_nbp(year) -> Dict[datetime, Clazz]:
    xls = config.EXANTE_PATH.joinpath(f'nbp_{year}.xls')
    workbook = xlrd.open_workbook(xls)
    sheet = workbook.sheet_by_name('Kursy średnie')
    return {
        xlrd.xldate_as_datetime(sheet.cell(i, 0).value, 0): Clazz(PLN=1.0,
                                                                  USD=sheet.cell(i, 2).value,
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
            trade_index[t.timestamp] += [Clazz(asset=t.asset, sum=float(t.sum))]
        symbol_trades[symbol] = trade_index

    return {k: dict(v) for k, v in symbol_trades.items()}


def calculate():
    exchange = CurrencyExchange()
    trades = sort_trades()
    closed_transactions = []
    total_profit = {}
    for symbol, time_transactions in trades.items():

        if symbol.endswith('.EXANTE') or symbol.endswith('.E.FX'):
            continue
        pprint(time_transactions, width=200)
        total_profit[symbol] = 0.0
        pending = []

        for timestamp, sub_transactions in time_transactions.items():

            tt = Clazz(time=to_datetime(timestamp))
            for t in sub_transactions:
                if symbol == t.asset:
                    tt.side = 1.0 if t.sum > 0 else -1.0
                    tt.quantity = abs(t.sum)
                else:
                    tt.value = abs(t.sum)
                    tt.currency = t.asset
            tt.unit_value = tt.value / tt.quantity
            pprint(tt, width=1000)

            for p in pending:
                if tt.quantity != 0.0 and p.side != tt.side:
                    quantity = 0.0
                    if p.quantity <= tt.quantity:
                        quantity = p.quantity
                        tt.quantity -= quantity
                        p.quantity = 0.0
                    elif p.quantity > tt.quantity:
                        quantity = tt.quantity
                        p.quantity -= quantity
                        tt.quantity = 0.0
                    unit_profit = p.side * (tt.unit_value - p.unit_value)
                    profit = quantity * unit_profit
                    open_value = quantity * p.unit_value
                    close_value = quantity * tt.unit_value
                    pln_exchange_value = exchange.value(tt.time, tt.currency)
                    total_profit[symbol] += profit
                    closed_transactions += [Clazz(symbol=symbol,
                                                  open_time=p.time,
                                                  close_time=tt.time,
                                                  quantity=quantity,
                                                  open_value=round(open_value, 4),
                                                  close_value=round(close_value, 4),
                                                  open_unit_value=round(p.unit_value, 4),
                                                  close_unit_value=round(tt.unit_value, 4),
                                                  profit=round(profit, 4),
                                                  currency=tt.currency,
                                                  pln_exchange_value=pln_exchange_value,
                                                  profit_pln=round(profit * pln_exchange_value, 4))]

            pending = [p for p in pending if p.quantity != 0]
            if tt.quantity != 0.0:
                pending += [tt]

    pprint(closed_transactions, width=400)
    pprint(total_profit, width=400)

    write_csv(TAX_TRANSACTIONS, closed_transactions)


def test_currency_exchange():
    exchange = CurrencyExchange()
    assert 3.6981 == exchange.value('2020-12-27 00:00:00', Currency.USD.name)


if __name__ == '__main__':
    # save_exante_transactions()
    # split_transactions()
    calculate()