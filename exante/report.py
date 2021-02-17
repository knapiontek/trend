from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pprint import pprint
from typing import Dict, List, Any, Tuple

import orjson as json
import pandas as pd
import xlrd
import xlwt

from src import exante, config, tool
from src.clazz import Clazz

EXANTE_TRANSACTIONS = 'exante_transactions'
TRADE_TRANSACTIONS = 'trade_transactions'

FEES = 'fees'
DIVIDENDS = 'dividends'
TRADES = 'trades'
FOREX = 'forex'
SUMMARY = 'summary'


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
        assert time.year in (2020, 2021)
        time -= timedelta(days=1)
        while time not in self.nbp:
            time -= timedelta(days=1)
            assert time.year in (2020, 2021)
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


def read_json(filename: str) -> List[Clazz]:
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


def split_exante_transactions():
    transactions = read_json(EXANTE_TRANSACTIONS)

    fees = [t for t in transactions if t.type in ('COMMISSION', 'INTEREST')]
    write_json(FEES, fees)
    write_csv(FEES, fees)

    dividends = [t for t in transactions if t.type in ('TAX', 'DIVIDEND')]
    write_json(DIVIDENDS, dividends)
    write_csv(DIVIDENDS, dividends)

    forex = [t for t in transactions if t.type == 'TRADE' and t.symbol.endswith('.E.FX')]
    write_json(FOREX, forex)
    write_csv(FOREX, forex)

    trades = [t for t in transactions
              if t.type == 'TRADE' and not t.symbol.endswith('.EXANTE') and not t.symbol.endswith('.E.FX')]
    write_json(TRADES, trades)
    write_csv(TRADES, trades)


def to_datetime(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp // 1000).isoformat(sep=' ')


def sort_trades() -> Dict[str, Dict]:
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


def calculate_trades() -> Dict[str, float]:
    exchange = CurrencyExchange()
    trades = sort_trades()

    closed_transactions = []
    total_pnl = {}
    for symbol, time_transactions in trades.items():
        total_pnl[symbol] = 0.0
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
                    unit_pnl = p.side * (tt.unit_value - p.unit_value)
                    pnl = quantity * unit_pnl
                    open_value = quantity * p.unit_value
                    close_value = quantity * tt.unit_value
                    pln_factor = exchange.value(tt.time, tt.currency)
                    profit_pln = pnl * pln_factor if pnl > 0.0 else 0.0
                    loss_pln = pnl * pln_factor if pnl <= 0.0 else 0.0
                    total_pnl[symbol] += pnl
                    closed_transactions += [Clazz(symbol=symbol,
                                                  open_time=p.time,
                                                  close_time=tt.time,
                                                  quantity=quantity,
                                                  open_value=round(open_value, 4),
                                                  close_value=round(close_value, 4),
                                                  open_unit_value=round(p.unit_value, 4),
                                                  close_unit_value=round(tt.unit_value, 4),
                                                  pnl=round(pnl, 4),
                                                  currency=tt.currency,
                                                  pln_factor=pln_factor,
                                                  profit_pln=round(profit_pln, 4),
                                                  loss_pln=round(loss_pln, 4))]

            pending = [p for p in pending if p.quantity != 0]
            if tt.quantity != 0.0:
                pending += [tt]

    write_json(TRADE_TRANSACTIONS, closed_transactions)
    write_csv(TRADE_TRANSACTIONS, closed_transactions)

    return {k: round(v, 4) for k, v in total_pnl.items()}


def test_currency_exchange():
    exchange = CurrencyExchange()
    assert 3.6981 == exchange.value('2020-12-27 00:00:00', Currency.USD.name)


def test_calculate_trades():
    trade_pnl = calculate_trades()
    pprint(trade_pnl)
    assert trade_pnl == {'DRW.ARCA': -16.0,
                         'EWS.ARCA': -101.0,
                         'FXF.ARCA': 7.36,
                         'GDXJ.ARCA': -27.6,
                         'KGH.WSE': -176.0,
                         'KRU.WSE': 234.0,
                         'OGZD.LSEIOB': -180.6,
                         'PKO.WSE': -380.0,
                         'PSLV.ARCA': 411.0,
                         'RSX.ARCA': 19.0,
                         'SDEM.ARCA': -9.4,
                         'SPY.ARCA': -15.9,
                         'VNQI.NASDAQ': -5.64,
                         'XME.ARCA': -0.8,
                         'XOM.NYSE': -49.6}


def copy_data(columns: Dict, sheet: Any, data: List[Dict]):
    for k, v in columns.items():
        row = sheet.row(0)
        row.write(v, k)
    for y, t in enumerate(data):
        row = sheet.row(y + 1)
        for k, v in columns.items():
            value = t[k]
            row.write(v, round(value, 2) if type(value) == float else value)


def create_trade_xls(trade_sheet) -> Tuple[float, float]:
    columns = dict(symbol=0,
                   open_time=1,
                   close_time=2,
                   quantity=3,
                   open_value=4,
                   close_value=5,
                   open_unit_value=6,
                   close_unit_value=7,
                   pnl=8,
                   currency=9,
                   pln_factor=10,
                   profit_pln=11,
                   loss_pln=12)

    trades = read_json(TRADE_TRANSACTIONS)
    copy_data(columns, trade_sheet, trades)

    profit_pln = sum([t.profit_pln for t in trades])
    loss_pln = sum([t.loss_pln for t in trades])
    row = trade_sheet.row(len(trades) + 3)
    row.write(0, 'Profit PLN')
    row.write(1, round(profit_pln, 2))
    row.write(3, 'Loss PLN')
    row.write(4, round(loss_pln, 2))

    return profit_pln, loss_pln


def create_forex_xls(forex_sheet) -> Tuple[float, float]:
    exchange = CurrencyExchange()

    columns = dict(currency=0,
                   pln_factor=1,
                   time=2,
                   pnl=3,
                   profit_pln=4,
                   loss_pln=5)

    forex = []
    for i in read_json(FOREX):
        if i.asset in ('PLN', 'USD', 'EUR'):
            time = to_datetime(i.timestamp)
            currency = i.asset
            pln_factor = exchange.value(time, currency)
            pnl = float(i.sum)
            profit_pln = pnl * pln_factor if pnl > 0.0 else 0.0
            loss_pln = pnl * pln_factor if pnl <= 0.0 else 0.0
            forex += [Clazz(currency=currency,
                            pln_factor=pln_factor,
                            time=time,
                            pnl=pnl,
                            profit_pln=profit_pln,
                            loss_pln=loss_pln)]

    copy_data(columns, forex_sheet, forex)

    profit_pln = sum([f.profit_pln for f in forex])
    loss_pln = sum([t.loss_pln for t in forex])
    row = forex_sheet.row(len(forex) + 3)
    row.write(0, 'Profit PLN')
    row.write(1, round(profit_pln, 2))
    row.write(3, 'Loss PLN')
    row.write(4, round(loss_pln, 2))

    return profit_pln, loss_pln


def create_fees_xls(fees_sheet) -> float:
    exchange = CurrencyExchange()

    columns = dict(currency=0,
                   pln_factor=1,
                   time=2,
                   loss=3,
                   loss_pln=4)

    fees = []
    for i in read_json(FEES):
        if i.asset in ('PLN', 'USD', 'EUR'):
            time = to_datetime(i.timestamp)
            currency = i.asset
            loss = float(i.sum)
            pln_factor = exchange.value(time, currency)
            loss_pln = loss * pln_factor
            fees += [Clazz(currency=currency, pln_factor=pln_factor, time=time, loss=loss, loss_pln=loss_pln)]

    copy_data(columns, fees_sheet, fees)

    loss_pln = sum([f.loss_pln for f in fees])
    row = fees_sheet.row(len(fees) + 3)
    row.write(0, 'Loss PLN')
    row.write(1, round(loss_pln, 2))

    return loss_pln


def create_dividends_xls(dividends_sheet) -> Tuple[float, float]:
    exchange = CurrencyExchange()

    columns = dict(symbol=0,
                   time=1,
                   currency=2,
                   pln_factor=3,
                   dividend=4,
                   tax=5,
                   dividend_pln=6,
                   tax_pln=7)

    dividends_index = defaultdict(Clazz)
    for i in read_json(DIVIDENDS):
        d = dividends_index[i.timestamp]
        currency = i.asset
        time = to_datetime(i.timestamp)
        pln_factor = exchange.value(time, currency)
        if i.type == 'DIVIDEND':
            d.symbol = i.symbol
            d.time = time
            d.currency = currency
            d.pln_factor = pln_factor
            d.dividend = float(i.sum)
            d.dividend_pln = d.dividend * pln_factor
            if 'tax' not in d:
                d.tax = 0.0
            if 'tax_pln' not in d:
                d.tax_pln = 0.0
        if i.type == 'TAX':
            d.tax = float(i.sum)
            d.tax_pln = d.tax * pln_factor

    dividends = list(dividends_index.values())
    copy_data(columns, dividends_sheet, dividends)

    dividend_pln = sum([d.dividend_pln for d in dividends])
    tax_pln = sum([d.tax_pln for d in dividends])
    row = dividends_sheet.row(len(dividends) + 3)
    row.write(0, 'Dividend PLN')
    row.write(1, round(dividend_pln, 2))
    row.write(3, 'Tax PLN')
    row.write(4, round(tax_pln, 2))

    return dividend_pln, tax_pln


def create_xls():
    book = xlwt.Workbook()

    summary_sheet = book.add_sheet("Summary")
    row = summary_sheet.row(0)
    row.write(1, 'Profit PLN')
    row.write(2, 'Loss PLN')
    row.write(3, 'Prepaid Tax PLN')

    trade_sheet = book.add_sheet("Trades")
    trade_profit_pln, trade_loss_pln = create_trade_xls(trade_sheet)
    row = summary_sheet.row(1)
    row.write(0, 'Trades')
    row.write(1, round(trade_profit_pln, 2))
    row.write(2, round(trade_loss_pln, 2))

    forex_sheet = book.add_sheet("Forex")
    forex_profit_pln, forex_loss_pln = create_forex_xls(forex_sheet)
    row = summary_sheet.row(2)
    row.write(0, 'Forex')
    row.write(1, round(forex_profit_pln, 2))
    row.write(2, round(forex_loss_pln, 2))

    fees_sheet = book.add_sheet("Fees")
    fees_pln = create_fees_xls(fees_sheet)
    row = summary_sheet.row(3)
    row.write(0, 'Fees')
    row.write(2, round(fees_pln, 2))

    dividends_sheet = book.add_sheet("Dividends")
    dividends_pln, tax_pln = create_dividends_xls(dividends_sheet)
    row = summary_sheet.row(4)
    row.write(0, 'Dividends')
    row.write(1, round(dividends_pln, 2))
    row.write(3, round(tax_pln, 2))

    row = summary_sheet.row(6)
    row.write(0, 'Total')
    row.write(1, round(trade_profit_pln + forex_profit_pln + dividends_pln, 2))
    row.write(2, round(trade_loss_pln + forex_loss_pln + fees_pln, 2))
    row.write(3, round(tax_pln, 2))

    path = config.STORE_PATH.joinpath(SUMMARY).with_suffix('.xls')
    book.save(path)


if __name__ == '__main__':
    save_exante_transactions()
    split_exante_transactions()
    test_currency_exchange()
    test_calculate_trades()
    create_xls()
