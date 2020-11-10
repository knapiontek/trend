import logging
from datetime import datetime, timezone

from src import tool, config


def test_exchange_holidays():
    for exchange in config.ACTIVE_EXCHANGES:
        result = tool.exchange_holidays(exchange)
        assert isinstance(result, set)


def test_last_workday():
    dt = datetime(2020, 1, 21, tzinfo=timezone.utc)
    assert tool.last_workday('NYSE', dt) == datetime(2020, 1, 17, tzinfo=timezone.utc)


def test_last_sunday():
    dt = datetime(2020, 9, 1, tzinfo=timezone.utc)
    assert tool.last_sunday(dt) == datetime(2020, 8, 30, tzinfo=timezone.utc)


def test_interval_name():
    assert tool.interval_name(tool.INTERVAL_1D) == '1d'


def test_time_slices_0():
    dt_from = datetime(2020, 8, 28, tzinfo=timezone.utc)
    dt_to = datetime(2020, 8, 28, 10, 12, 10, tzinfo=timezone.utc)
    slices = [(tool.dt_format(slice_from), tool.dt_format(slice_to))
              for slice_from, slice_to in tool.time_slices(dt_from, dt_to, tool.INTERVAL_1D, 14)]
    assert slices == []


def test_time_slices_1():
    dt_from = datetime(2020, 8, 28, tzinfo=timezone.utc)
    dt_to = datetime(2020, 8, 28, 10, 12, 10, tzinfo=timezone.utc)
    slices = [(tool.dt_format(slice_from), tool.dt_format(slice_to))
              for slice_from, slice_to in tool.time_slices(dt_from, dt_to, tool.INTERVAL_1H, 14)]
    assert slices == [('2020-08-28 01:00:00 +0000', '2020-08-28 10:12:10 +0000')]


def test_time_slices():
    dt_from = datetime(2020, 2, 1, tzinfo=timezone.utc)
    dt_to = datetime(2020, 2, 4, tzinfo=timezone.utc)
    slices = [(tool.dt_format(start), tool.dt_format(stop))
              for start, stop in tool.time_slices(dt_from, dt_to, tool.INTERVAL_1H, 21)]
    assert slices == [
        ('2020-02-01 01:00:00 +0000', '2020-02-01 21:00:00 +0000'),
        ('2020-02-01 22:00:00 +0000', '2020-02-02 18:00:00 +0000'),
        ('2020-02-02 19:00:00 +0000', '2020-02-03 15:00:00 +0000'),
        ('2020-02-03 16:00:00 +0000', '2020-02-04 00:00:00 +0000')
    ]


def test_transpose():
    result = tool.transpose([tool.Clazz(key='v1'), tool.Clazz(key='v2')], ['key'])
    assert result == {'key': ['v1', 'v2']}


def test_no_exception(caplog):
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)

    @tool.catch_exception(log)
    def function_x():
        return None

    function_x()
    assert 'function_x done' in caplog.text


def test_catch_exception(caplog):
    log = logging.getLogger(__name__)

    @tool.catch_exception(log)
    def function_x():
        return 1 / 0

    function_x()
    assert 'function_x failed' in caplog.text
