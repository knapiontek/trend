from datetime import timedelta, datetime

from src import tools, session, config


def test_time_series():
    symbol = 'XOM.NYSE'
    dt_from = datetime(2020, 2, 3)
    dt_to = datetime(2020, 2, 5)
    delta = timedelta(hours=14)
    close_prices = []
    with session.ExanteSession() as exante:
        for start, stop in tools.time_slices(dt_from, delta, dt_to):
            series = exante.series(symbol, start, stop, duration=config.DURATION_1H)
            close_prices += [(c['utc'], c['close']) for c in series]
    assert close_prices == [
        ('2020-02-03 09:00:00+0000', '61.53'),
        ('2020-02-03 10:00:00+0000', '61.55'),
        ('2020-02-03 11:00:00+0000', '61.61'),
        ('2020-02-03 12:00:00+0000', '61.69'),
        ('2020-02-03 13:00:00+0000', '61.53'),
        ('2020-02-03 14:00:00+0000', '61.011'),
        ('2020-02-03 14:00:00+0000', '61.011'),
        ('2020-02-03 15:00:00+0000', '60.97'),
        ('2020-02-03 16:00:00+0000', '60.715'),
        ('2020-02-03 17:00:00+0000', '60.665'),
        ('2020-02-03 18:00:00+0000', '60.565'),
        ('2020-02-03 19:00:00+0000', '60.44'),
        ('2020-02-03 20:00:00+0000', '60.72'),
        ('2020-02-03 21:00:00+0000', '60.65'),
        ('2020-02-03 22:00:00+0000', '60.65'),
        ('2020-02-03 23:00:00+0000', '60.68'),
        ('2020-02-04 00:00:00+0000', '60.6899'),
        ('2020-02-04 09:00:00+0000', '61.63'),
        ('2020-02-04 10:00:00+0000', '61.79'),
        ('2020-02-04 11:00:00+0000', '61.57'),
        ('2020-02-04 12:00:00+0000', '61.59'),
        ('2020-02-04 13:00:00+0000', '61.61'),
        ('2020-02-04 14:00:00+0000', '61.0894'),
        ('2020-02-04 15:00:00+0000', '60.805'),
        ('2020-02-04 16:00:00+0000', '60.715'),
        ('2020-02-04 17:00:00+0000', '60.37'),
        ('2020-02-04 18:00:00+0000', '60.13'),
        ('2020-02-04 18:00:00+0000', '60.13'),
        ('2020-02-04 19:00:00+0000', '60.06'),
        ('2020-02-04 20:00:00+0000', '59.97'),
        ('2020-02-04 21:00:00+0000', '59.86'),
        ('2020-02-04 22:00:00+0000', '59.94'),
        ('2020-02-04 23:00:00+0000', '59.97'),
        ('2020-02-05 00:00:00+0000', '59.94')
    ]
