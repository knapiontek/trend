from src import web, tools


def test_filter():
    instruments = [
        {
            'optionData': None,
            'i18n': {},
            'name': 'Exxon Mobil Corporation',
            'symbolId': 'XOM.NYSE',
            'description': 'Exxon Mobil Corporation Common Stock',
            'country': 'US', 'exchange': 'NYSE',
            'symbolType': 'STOCK',
            'currency': 'USD',
            'minPriceIncrement': '0.01',
            'ticker': 'XOM',
            'expiration': None,
            'group': None
        }
    ]
    filter_query = '{currency} contains usd && {symbolType} contains stock && {symbolId} contains xom'
    filtered = web.filter_instruments(instruments, filter_query=filter_query)
    assert len(filtered) == 1

    selected = [i for i in tools.dict_it(filtered, ('symbolId', 'country'))]
    assert len(selected) == 1
