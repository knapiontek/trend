from datetime import datetime, timezone

from src import stooq, tools


def test_series():
    interval = tools.INTERVAL_1D
    dt_from = datetime(2020, 2, 2, 23, tzinfo=timezone.utc)
    dt_to = datetime(2020, 2, 4, 19, tzinfo=timezone.utc)
    with stooq.Session({'WSE': [interval]}) as session:
        series = session.series('KGH.WSE', dt_from, dt_to, interval)

    closing_prices = [
        (tools.ts_format(timestamp), close, volume)
        for timestamp, close, volume in tools.tuple_it(series, ('timestamp', 'close', 'volume'))
    ]

    assert closing_prices == [('2020-02-03 00:00:00 +0000', 92.6, 484464), ('2020-02-04 00:00:00 +0000', 96.44, 708829)]
