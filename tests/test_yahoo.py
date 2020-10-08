from datetime import datetime, timezone

from src import yahoo, tools


def test_series():
    interval = tools.INTERVAL_1D
    dt_from = datetime(2020, 2, 2, tzinfo=timezone.utc)
    dt_to = datetime(2020, 2, 4, tzinfo=timezone.utc)
    with yahoo.Session() as session:
        series = session.series('XOM.NYSE', dt_from, dt_to, interval)

    closing_prices = [
        (tools.ts_format(timestamp), close, volume)
        for timestamp, close, volume in tools.tuple_it(series, ('timestamp', 'close', 'volume'))
    ]

    assert closing_prices == [
        ('2020-02-03 00:00:00 +0000', 60.73, 27397300),
        ('2020-02-04 00:00:00 +0000', 59.970001, 31922100)
    ]
