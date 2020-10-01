import jsonschema

from src import data, store, config


def test_exchanges():
    data.exchange_update()
    with store.Exchanges() as db_exchanges:
        for name in config.ACTIVE_EXCHANGES:
            instruments = db_exchanges[name]
            assert len(instruments) > 16
            for instrument in instruments:
                document = {k: v for k, v in instrument.items() if k not in ('_rev', '_id', '_key')}
                jsonschema.validate(document, store.EXCHANGE_SCHEMA['rule'])
