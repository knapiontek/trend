from src import store


def test_editable():
    city = 'Dublin'
    city_key = 'city'
    store_name = 'test_info'

    with store.FileStore(store_name, editable=True) as info:
        info[city_key] = city

    with store.FileStore(store_name, editable=False) as info:
        assert info[city_key] == city

    try:
        with store.FileStore('test_info', editable=False) as info:
            info[city_key] = city
    except:
        pass
    else:
        assert False


def test_columns():
    with store.FileStore('S&P500') as sp500:
        for symbol, security, location in sp500.read(columns=['Symbol', 'Security', 'Headquarters Location']):
            if symbol == 'ZTS':
                assert security == 'Zoetis'
                assert location == 'Florham Park, New Jersey'
