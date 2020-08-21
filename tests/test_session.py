from datetime import timedelta, datetime

from src import tools


def test_time_slices():
    begin = datetime(2020, 2, 1)
    end = datetime(2020, 2, 4)
    delta = timedelta(hours=4)
    for start, stop in tools.time_slices(begin, delta, end):
        assert stop - start <= delta
