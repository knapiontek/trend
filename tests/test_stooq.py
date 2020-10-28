from datetime import datetime, timezone

from src import stooq, tool


def test_series():
    interval = tool.INTERVAL_1D
    dt_from = datetime(2020, 2, 2, tzinfo=timezone.utc)
    dt_to = datetime(2020, 2, 4, tzinfo=timezone.utc)
    with stooq.Session({'XETRA': [interval]}) as session:
        series = session.series('SIE.XETRA', dt_from, dt_to, interval)

    closing_prices = [(tool.ts_format(s.timestamp), s.close, s.volume) for s in series]

    assert closing_prices == [('2020-02-03 00:00:00 +0000', 107.41, 2466371),
                              ('2020-02-04 00:00:00 +0000', 109.11, 2416826)]
