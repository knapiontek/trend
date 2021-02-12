from pprint import pprint

from src import exante


def analyse_transactions():
    with exante.Session() as session:
        transactions = session.transactions()
        for t in transactions:
            if t.type == 'TRADE' and t.symbol == 'KRU.WSE':
                pprint(t)


if __name__ == '__main__':
    analyse_transactions()
