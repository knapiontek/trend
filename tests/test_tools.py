from datetime import timedelta, datetime

from src import tools, config


def test_list_split():
    lst = [1, 2, 3, 4, 5, 'PSLV.ARCA']

    chunks = [chunk for chunk in tools.list_split(lst, 5)]
    assert chunks == [[1, 2, 3, 4, 5], ['PSLV.ARCA']]

    chunks = [chunk for chunk in tools.list_split(lst, 3)]
    assert chunks == [[1, 2, 3], [4, 5, 'PSLV.ARCA']]


def test_time_slices_0():
    dt_from = datetime(2020, 8, 28)
    dt_to = datetime(2020, 8, 28, 10, 12, 10)
    slice_delta = timedelta(days=14)
    time_delta = timedelta(seconds=config.DURATION_1D)
    slices = [(tools.dt_format(start), tools.dt_format(stop))
              for start, stop in tools.time_slices(dt_from, dt_to, slice_delta, time_delta)]
    assert slices == []


def test_time_slices_1():
    dt_from = datetime(2020, 8, 28)
    dt_to = datetime(2020, 8, 28, 10, 12, 10)
    slice_delta = timedelta(hours=14)
    time_delta = timedelta(seconds=config.DURATION_1H)
    slices = [(tools.dt_format(start), tools.dt_format(stop))
              for start, stop in tools.time_slices(dt_from, dt_to, slice_delta, time_delta)]
    assert slices == [('2020-08-28 01:00:00', '2020-08-28 10:12:10')]


def test_time_slices():
    dt_from = datetime(2020, 2, 1)
    dt_to = datetime(2020, 2, 4)
    slice_delta = timedelta(hours=21)
    time_delta = timedelta(seconds=config.DURATION_1H)
    slices = [(tools.dt_format(start), tools.dt_format(stop))
              for start, stop in tools.time_slices(dt_from, dt_to, slice_delta, time_delta)]
    assert slices == [
        ('2020-02-01 01:00:00', '2020-02-01 21:00:00'),
        ('2020-02-01 22:00:00', '2020-02-02 18:00:00'),
        ('2020-02-02 19:00:00', '2020-02-03 15:00:00'),
        ('2020-02-03 16:00:00', '2020-02-04 00:00:00')
    ]
