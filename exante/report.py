from collections import defaultdict
from pprint import pprint
from typing import Dict, List

import pandas as pd

from src import exante, store, config
from src.clazz import Clazz

EXANTE_TRANSACTIONS = 'exante_transactions'
ORIGINAL = 'original'
COMMISSIONS = 'commissions'
DIVIDEND = 'dividend'


def json_to_csv(filename: str, content: List[Dict]):
    df = pd.DataFrame(content)
    path = config.STORE_PATH.joinpath(filename).with_suffix('.csv')
    df.to_csv(path, index=False, header=True)


def save_exante_transactions():
    with exante.Session() as session:
        transactions = session.transactions()
        with store.File(EXANTE_TRANSACTIONS, editable=True) as exante_transactions:
            exante_transactions[ORIGINAL] = transactions


def analyse_exante_transactions():
    with store.File(EXANTE_TRANSACTIONS) as exante_transactions:
        transactions = exante_transactions[ORIGINAL]
        json_to_csv(EXANTE_TRANSACTIONS, transactions)

    with store.File(COMMISSIONS, editable=True) as commissions:
        commissions[ORIGINAL] = [t for t in transactions if t['type'] in ('COMMISSION', 'INTEREST')]

    with store.File(DIVIDEND, editable=True) as taxes:
        taxes[ORIGINAL] = [t for t in transactions if t['type'] in ('TAX', 'DIVIDEND')]

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
    analyse_exante_transactions()
