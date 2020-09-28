from datetime import datetime, timezone

from src import stooq, tools


def test_series():
    interval = tools.INTERVAL_1D
    dt_from = datetime(2020, 2, 2, 23, tzinfo=timezone.utc)
    dt_to = datetime(2020, 2, 4, 19, tzinfo=timezone.utc)
    with stooq.Session(['NYSE']) as session:
        series = session.series('XOM.NYSE', dt_from, dt_to, interval)

    closing_prices = [
        (tools.ts_format(timestamp), close, volume)
        for timestamp, close, volume in tools.tuple_it(series, ('timestamp', 'close', 'volume'))
    ]

    assert closing_prices == [
        ('2020-02-03 09:00:00 +0000', 61.53, 11021),
        ('2020-02-03 10:00:00 +0000', 61.55, 700),
        ('2020-02-03 11:00:00 +0000', 61.61, 7100),
        ('2020-02-03 12:00:00 +0000', 61.69, 9668),
    ]
