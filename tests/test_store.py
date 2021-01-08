from src import store


def test_editable():
    city = 'Dublin'
    city_key = 'city'
    store_name = 'test_info'

    with store.File(store_name, editable=True) as info:
        info[city_key] = city

    with store.File(store_name, editable=False) as info:
        assert info[city_key] == city

    try:
        with store.File('test_info', editable=False) as info:
            info[city_key] = city
    except:
        pass
    else:
        assert False
