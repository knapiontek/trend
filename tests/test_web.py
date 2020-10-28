from src import web


def test_select():
    instruments = [
        {
            'name': 'Exxon Mobil Corporation',
            'symbol': 'XOM.NYSE',
            'description': 'Exxon Mobil Corporation Common Stock',
            'country': 'US',
            'exchange': 'NYSE',
            'type': 'STOCK',
            'currency': 'USD'
        }
    ]
    query = '{currency} contains usd && {type} contains stock && {symbol} contains xom'
    selected = web.select_instruments(instruments, query=query)
    assert len(selected) == 1
