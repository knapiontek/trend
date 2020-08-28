from datetime import timedelta, datetime

from src import tools, session, config


def test_time_series():
    symbol = 'XOM.NYSE'
    duration = config.DURATION_1H
    dt_from = datetime(2020, 2, 2, 23)
    dt_to = datetime(2020, 2, 4, 19)
    slice_delta = timedelta(hours=15)
    time_delta = timedelta(seconds=duration)

    time_ranges = []
    closing_prices = []

    with session.ExanteSession() as exante:
        for start, stop in tools.time_slices(dt_from, dt_to, slice_delta, time_delta):
            series = exante.series(symbol, start, stop, duration)
            time_ranges += [(tools.dt_format(start), tools.dt_format(stop))]
            closing_prices += [(c['utc'], c['close'], c['volume']) for c in series]

    assert time_ranges == [
        ('2020-02-03 00:00:00', '2020-02-03 14:00:00'),
        ('2020-02-03 15:00:00', '2020-02-04 05:00:00'),
        ('2020-02-04 06:00:00', '2020-02-04 19:00:00')
    ]

    assert closing_prices == [
        ('2020-02-03 09:00:00+0000', '61.53', '11021'),
        ('2020-02-03 10:00:00+0000', '61.55', '700'),
        ('2020-02-03 11:00:00+0000', '61.61', '7100'),
        ('2020-02-03 12:00:00+0000', '61.69', '9668'),
        ('2020-02-03 13:00:00+0000', '61.53', '64526'),
        ('2020-02-03 14:00:00+0000', '61.011', '4168908'),
        ('2020-02-03 15:00:00+0000', '60.97', '3386157'),
        ('2020-02-03 16:00:00+0000', '60.715', '3654783'),
        ('2020-02-03 17:00:00+0000', '60.665', '2188951'),
        ('2020-02-03 18:00:00+0000', '60.565', '2081716'),
        ('2020-02-03 19:00:00+0000', '60.44', '1960787'),
        ('2020-02-03 20:00:00+0000', '60.72', '4368450'),
        ('2020-02-03 21:00:00+0000', '60.65', '2567304'),
        ('2020-02-03 22:00:00+0000', '60.65', '2450'),
        ('2020-02-03 23:00:00+0000', '60.68', '4489'),
        ('2020-02-04 00:00:00+0000', '60.6899', '1866'),
        ('2020-02-04 09:00:00+0000', '61.63', '1649'),
        ('2020-02-04 10:00:00+0000', '61.79', '4457'),
        ('2020-02-04 11:00:00+0000', '61.57', '3021'),
        ('2020-02-04 12:00:00+0000', '61.59', '19546'),
        ('2020-02-04 13:00:00+0000', '61.61', '124873'),
        ('2020-02-04 14:00:00+0000', '61.0894', '2839556'),
        ('2020-02-04 15:00:00+0000', '60.805', '3411238'),
        ('2020-02-04 16:00:00+0000', '60.715', '2728185'),
        ('2020-02-04 17:00:00+0000', '60.37', '3187416'),
        ('2020-02-04 18:00:00+0000', '60.13', '2743043'),
        ('2020-02-04 19:00:00+0000', '60.06', '2958939'),
    ]
