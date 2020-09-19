from src import web, tools


def test_filter():
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
    filter_query = '{currency} contains usd && {type} contains stock && {symbol} contains xom'
    filtered = web.filter_instruments(instruments, filter_query=filter_query)
    assert len(filtered) == 1

    selected = [i for i in tools.dict_it(filtered, ('symbol', 'country'))]
    assert len(selected) == 1
