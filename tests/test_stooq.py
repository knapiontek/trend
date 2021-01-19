from datetime import datetime, timezone

from src import stooq, tool
from src.tool import DateTime


def test_series():
    interval = tool.INTERVAL_1D
    dt_from = datetime(2020, 2, 2, tzinfo=timezone.utc)
    dt_to = datetime(2020, 2, 4, tzinfo=timezone.utc)
    with stooq.Session({'WSE': [interval]}) as session:
        series = session.series('KGH.WSE', dt_from, dt_to, interval)

    closing_prices = [(DateTime.format(s.timestamp), s.close, s.volume) for s in series]

    assert closing_prices == [
        ('2020-02-03 00:00:00 +0000', 92.6, 484464),
        ('2020-02-04 00:00:00 +0000', 96.44, 708829)
    ]


def test_securities():
    symbol = 'XOM.NYSE'
    interval = tool.INTERVAL_1D
    with stooq.SecuritySeries(interval) as security_series:
        time_series = security_series[symbol]
    assert len(time_series) >= 1000
