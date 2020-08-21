from datetime import timedelta, datetime

from src import tools


def test_list_split():
    lst = [1, 2, 3, 4, 5, 'PSLV.ARCA']

    chunks = [chunk for chunk in tools.list_split(lst, 5)]
    assert chunks == [[1, 2, 3, 4, 5], ['PSLV.ARCA']]

    chunks = [chunk for chunk in tools.list_split(lst, 3)]
    assert chunks == [[1, 2, 3], [4, 5, 'PSLV.ARCA']]


def test_time_slices():
    begin = datetime(2020, 2, 1)
    end = datetime(2020, 2, 4)
    delta = timedelta(hours=21)
    slices = [(tools.dt_format(start), tools.dt_format(stop)) for start, stop in tools.time_slices(begin, delta, end)]
    assert slices == [
        ('2020-02-01 00:00:01', '2020-02-01 21:00:00'),
        ('2020-02-01 21:00:01', '2020-02-02 18:00:00'),
        ('2020-02-02 18:00:01', '2020-02-03 15:00:00'),
        ('2020-02-03 15:00:01', '2020-02-04 12:00:00')
    ]
