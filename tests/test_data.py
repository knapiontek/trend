import jsonschema

from src import data, store, config


def test_exchanges():
    data.exchange_update()
    with store.Exchanges() as db_exchanges:
        for name in config.ACTIVE_EXCHANGES:
            instruments = db_exchanges[name]
            assert len(instruments) > 64
            for instrument in instruments:
                jsonschema.validate(instrument, store.EXCHANGE_SCHEMA['rule'])
