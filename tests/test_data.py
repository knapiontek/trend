import jsonschema

from src import data, store, config


def test_exchanges():
    data.exchange_update()
    with store.FileStore('exchanges') as content:
        for exchange in config.ACTIVE_EXCHANGES:
            instruments = content[exchange]
            assert len(instruments) > 100
            for instrument in instruments:
                jsonschema.validate(instrument, store.EXCHANGE_SCHEMA['rule'])
