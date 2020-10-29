import jsonschema

from src import data, store, config


def test_exchanges():
    data.exchange_update()
    with store.ExchangeSeries() as db_exchanges:
        for name in config.ACTIVE_EXCHANGES:
            securities = db_exchanges[name]
            assert len(securities) > 16
            for security in securities:
                document = {k: v for k, v in security.items() if k not in ('_rev', '_id', '_key')}
                jsonschema.validate(document, store.EXCHANGE_SCHEMA['rule'])
