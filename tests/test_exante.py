from pprint import pprint

from src import tool, exante
from src.tool import DateTime


def test_securities():
    symbol = 'XOM.NYSE'
    interval = tool.INTERVAL_1D
    with exante.SecuritySeries(interval) as security_series:
        time_series = security_series[symbol]
    assert len(time_series) >= 1000


def test_series():
    symbol = 'XOM.NYSE'
    interval = tool.INTERVAL_1H
    dt_from = DateTime(2020, 2, 2, 23)
    dt_to = DateTime(2020, 2, 4, 19)

    time_ranges = []
    closing_prices = []

    with exante.Session() as session:
        for slice_from, slice_to in tool.time_slices(dt_from, dt_to, interval, 15):
            series = session.series(symbol, slice_from, slice_to, interval)
            time_ranges += [(slice_from.format(), slice_to.format())]
            closing_prices += [(DateTime.from_timestamp(s.timestamp).format(), s.close, s.volume) for s in series]

    assert time_ranges == [
        ('2020-02-03 00:00:00', '2020-02-03 14:00:00'),
        ('2020-02-03 15:00:00', '2020-02-04 05:00:00'),
        ('2020-02-04 06:00:00', '2020-02-04 19:00:00')
    ]

    assert closing_prices == [
        ('2020-02-03 09:00:00', 61.53, 11021),
        ('2020-02-03 10:00:00', 61.55, 700),
        ('2020-02-03 11:00:00', 61.61, 7100),
        ('2020-02-03 12:00:00', 61.69, 9668),
        ('2020-02-03 13:00:00', 61.53, 64526),
        ('2020-02-03 14:00:00', 61.011, 4168908),
        ('2020-02-03 15:00:00', 60.97, 3386157),
        ('2020-02-03 16:00:00', 60.715, 3654783),
        ('2020-02-03 17:00:00', 60.665, 2188951),
        ('2020-02-03 18:00:00', 60.565, 2081716),
        ('2020-02-03 19:00:00', 60.44, 1960787),
        ('2020-02-03 20:00:00', 60.72, 4368450),
        ('2020-02-03 21:00:00', 60.65, 2567304),
        ('2020-02-03 22:00:00', 60.65, 2450),
        ('2020-02-03 23:00:00', 60.68, 4489),
        ('2020-02-04 00:00:00', 60.6899, 1866),
        ('2020-02-04 09:00:00', 61.63, 1649),
        ('2020-02-04 10:00:00', 61.79, 4457),
        ('2020-02-04 11:00:00', 61.57, 3021),
        ('2020-02-04 12:00:00', 61.59, 19546),
        ('2020-02-04 13:00:00', 61.61, 124873),
        ('2020-02-04 14:00:00', 61.0894, 2839556),
        ('2020-02-04 15:00:00', 60.805, 3411238),
        ('2020-02-04 16:00:00', 60.715, 2728185),
        ('2020-02-04 17:00:00', 60.37, 3187416),
        ('2020-02-04 18:00:00', 60.13, 2743043),
        ('2020-02-04 19:00:00', 60.06, 2958939)
    ]


def test_transactions():
    with exante.Session() as session:
        transactions = session.transactions()
        pprint(transactions)
    assert len(transactions) >= 0


def test_orders():
    with exante.Session() as session:
        orders = session.orders()
    assert len(orders) >= 0


def _test_order():
    with exante.Session() as session:
        session.order(symbol='TOA.WSE', limit=6.48, stop_loss=4.0)
