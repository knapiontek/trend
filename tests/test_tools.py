from datetime import timedelta, datetime

from src import tools, config


def test_list_split():
    lst = [1, 2, 3, 4, 5, 'PSLV.ARCA']

    chunks = [chunk for chunk in tools.list_split(lst, 5)]
    assert chunks == [[1, 2, 3, 4, 5], ['PSLV.ARCA']]

    chunks = [chunk for chunk in tools.list_split(lst, 3)]
    assert chunks == [[1, 2, 3], [4, 5, 'PSLV.ARCA']]


def test_time_slices():
    dt_from = datetime(2020, 2, 1)
    dt_to = datetime(2020, 2, 4)
    delta = timedelta(hours=21)
    slices = [(tools.dt_format(start), tools.dt_format(stop))
              for start, stop in tools.time_slices(dt_from, dt_to, delta, config.DURATION_1H)]
    assert slices == [
        ('2020-02-01 00:00:00', '2020-02-01 21:00:00'),
        ('2020-02-01 22:00:00', '2020-02-02 18:00:00'),
        ('2020-02-02 19:00:00', '2020-02-03 15:00:00'),
        ('2020-02-03 16:00:00', '2020-02-04 00:00:00')
    ]
