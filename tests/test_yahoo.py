from datetime import datetime, timezone

from src import yahoo, tool
from src.tool import DateTime


def test_series():
    interval = tool.INTERVAL_1D
    dt_from = datetime(2020, 2, 2, tzinfo=timezone.utc)
    dt_to = datetime(2020, 2, 4, tzinfo=timezone.utc)
    with yahoo.Session() as session:
        series = session.series('XOM.NYSE', dt_from, dt_to, interval)

    closing_prices = [(DateTime.format(s.timestamp), s.close, s.volume) for s in series]

    assert closing_prices == [
        ('2020-02-03 00:00:00 +0000', 60.73, 27397300),
        ('2020-02-04 00:00:00 +0000', 59.970001, 31922100)
    ]


def test_securities():
    symbol = 'XOM.NYSE'
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        time_series = security_series[symbol]
    assert len(time_series) >= 1000
