from datetime import datetime, timezone

from src import tools


def test_last_workday():
    dt = datetime(2020, 1, 21, tzinfo=timezone.utc)
    assert tools.last_workday('NYSE', dt) == datetime(2020, 1, 17, tzinfo=timezone.utc)


def test_last_sunday():
    dt = datetime(2020, 9, 1, tzinfo=timezone.utc)
    assert tools.last_sunday(dt) == datetime(2020, 8, 30, tzinfo=timezone.utc)


def test_interval_name():
    assert tools.interval_name(tools.INTERVAL_1D) == '1d'


def test_list_split():
    lst = [1, 2, 3, 4, 5, 'PSLV.ARCA']

    chunks = [chunk for chunk in tools.list_split(lst, 5)]
    assert chunks == [[1, 2, 3, 4, 5], ['PSLV.ARCA']]

    chunks = [chunk for chunk in tools.list_split(lst, 3)]
    assert chunks == [[1, 2, 3], [4, 5, 'PSLV.ARCA']]


def test_time_slices_0():
    dt_from = datetime(2020, 8, 28, tzinfo=timezone.utc)
    dt_to = datetime(2020, 8, 28, 10, 12, 10, tzinfo=timezone.utc)
    slices = [(tools.dt_format(slice_from), tools.dt_format(slice_to))
              for slice_from, slice_to in tools.time_slices(dt_from, dt_to, tools.INTERVAL_1D, 14)]
    assert slices == []


def test_time_slices_1():
    dt_from = datetime(2020, 8, 28, tzinfo=timezone.utc)
    dt_to = datetime(2020, 8, 28, 10, 12, 10, tzinfo=timezone.utc)
    slices = [(tools.dt_format(slice_from), tools.dt_format(slice_to))
              for slice_from, slice_to in tools.time_slices(dt_from, dt_to, tools.INTERVAL_1H, 14)]
    assert slices == [('2020-08-28 01:00:00 +0000', '2020-08-28 10:12:10 +0000')]


def test_time_slices():
    dt_from = datetime(2020, 2, 1, tzinfo=timezone.utc)
    dt_to = datetime(2020, 2, 4, tzinfo=timezone.utc)
    slices = [(tools.dt_format(start), tools.dt_format(stop))
              for start, stop in tools.time_slices(dt_from, dt_to, tools.INTERVAL_1H, 21)]
    assert slices == [
        ('2020-02-01 01:00:00 +0000', '2020-02-01 21:00:00 +0000'),
        ('2020-02-01 22:00:00 +0000', '2020-02-02 18:00:00 +0000'),
        ('2020-02-02 19:00:00 +0000', '2020-02-03 15:00:00 +0000'),
        ('2020-02-03 16:00:00 +0000', '2020-02-04 00:00:00 +0000')
    ]


def test_transpose():
    result = tools.transpose([{'key': 'v1'}, {'key': 'v2'}], ['key'])
    assert result == {'key': ['v1', 'v2']}


FRAME1 = {'schema': ['key1', 'key2'], 'data': [['v11', 'v12'], ['v21', 'v22']]}
FRAME2 = [{'k1': 'v1', 'k2': 'v2'}]


def test_tuple_it():
    result1 = [k1 for k1 in tools.tuple_it(FRAME1, ['key1'])]
    assert result1 == [('v11',), ('v21',)]

    result2 = [(k1, k2) for k1, k2 in tools.tuple_it(FRAME1, ['key1', 'key2'])]
    assert result2 == [('v11', 'v12'), ('v21', 'v22')]

    for v1, v2 in tools.tuple_it(FRAME2, ['k1', 'k2']):
        assert v1 == 'v1'
        assert v2 == 'v2'


def test_dict_it():
    result1 = [k1 for k1 in tools.dict_it(FRAME1, ['key1'])]
    assert result1 == [{'key1': 'v11'}, {'key1': 'v21'}]

    result2 = [dt for dt in tools.dict_it(FRAME1, ['key1', 'key2'])]
    assert result2 == [{'key1': 'v11', 'key2': 'v12'}, {'key1': 'v21', 'key2': 'v22'}]

    for dt in tools.dict_it(FRAME2, ['k1']):
        assert dt == {'k1': 'v1'}


def test_loop_it():
    result1 = [v1 for v1 in tools.loop_it(FRAME1, 'key1')]
    assert result1 == ['v11', 'v21']

    for v1 in tools.loop_it(FRAME2, 'k1'):
        assert v1 == 'v1'


def test_progress():
    lst = [1, 2]
    with tools.Progress(test_progress.__name__, lst) as progress:
        progress('1')
        progress('2')
