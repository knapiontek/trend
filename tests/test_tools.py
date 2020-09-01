from datetime import timedelta, datetime

from src import tools


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
    time_delta = timedelta(seconds=tools.DURATION_1D)
    slices = [(tools.dt_format(start), tools.dt_format(stop))
              for start, stop in tools.time_slices(dt_from, dt_to, slice_delta, time_delta)]
    assert slices == []


def test_time_slices_1():
    dt_from = datetime(2020, 8, 28)
    dt_to = datetime(2020, 8, 28, 10, 12, 10)
    slice_delta = timedelta(hours=14)
    time_delta = timedelta(seconds=tools.DURATION_1H)
    slices = [(tools.dt_format(start), tools.dt_format(stop))
              for start, stop in tools.time_slices(dt_from, dt_to, slice_delta, time_delta)]
    assert slices == [('2020-08-28 01:00:00', '2020-08-28 10:12:10')]


def test_time_slices():
    dt_from = datetime(2020, 2, 1)
    dt_to = datetime(2020, 2, 4)
    slice_delta = timedelta(hours=21)
    time_delta = timedelta(seconds=tools.DURATION_1H)
    slices = [(tools.dt_format(start), tools.dt_format(stop))
              for start, stop in tools.time_slices(dt_from, dt_to, slice_delta, time_delta)]
    assert slices == [
        ('2020-02-01 01:00:00', '2020-02-01 21:00:00'),
        ('2020-02-01 22:00:00', '2020-02-02 18:00:00'),
        ('2020-02-02 19:00:00', '2020-02-03 15:00:00'),
        ('2020-02-03 16:00:00', '2020-02-04 00:00:00')
    ]


def test_transpose():
    result = tools.transpose([{'key': 'v1'}, {'key': 'v2'}], ['key'])
    assert result == {'key': ['v1', 'v2']}


FRAME1 = {'schema': ['key1', 'key2'], 'data': [['v11', 'v12'], ['v21', 'v22']]}
FRAME2 = [{'k1': 'v1', 'k2': 'v2'}]


def test_tuples():
    result1 = [k1 for k1 in tools.tuples(FRAME1, ['key1'])]
    assert result1 == [('v11',), ('v21',)]

    result2 = [(k1, k2) for k1, k2 in tools.tuples(FRAME1, ['key1', 'key2'])]
    assert result2 == [('v11', 'v12'), ('v21', 'v22')]

    for v1, v2 in tools.tuples(FRAME2, ['k1', 'k2']):
        assert v1 == 'v1'
        assert v2 == 'v2'


def test_dicts():
    result1 = [k1 for k1 in tools.dicts(FRAME1, ['key1'])]
    assert result1 == [{'key1': 'v11'}, {'key1': 'v21'}]

    result2 = [item for item in tools.dicts(FRAME1, ['key1', 'key2'])]
    assert result2 == [{'key1': 'v11', 'key2': 'v12'}, {'key1': 'v21', 'key2': 'v22'}]

    for item in tools.dicts(FRAME2, ['k1']):
        assert item == {'k1': 'v1'}


def test_progress():
    progress = tools.Progress(test_progress.__name__, length=2)
    progress += 1
    progress += 1
    assert progress.count == progress.length
