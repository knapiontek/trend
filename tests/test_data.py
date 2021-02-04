import jsonschema

from src import data, store, config, schema


def test_exchanges():
    data.exchange_update()
    with store.ExchangeSeries() as exchange_series:
        for name in config.EXCHANGES:
            securities = exchange_series[name]
            assert len(securities) > 16
            for security in securities:
                document = {k: v for k, v in security.items() if k not in ('_rev', '_id', '_key')}
                jsonschema.validate(document, schema.EXCHANGE_SCHEMA['rule'])


def _test_security_update():
    import src.exante as engine
    data.security_update(engine)
