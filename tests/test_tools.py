import logging

from src import tool, config
from src.clazz import Clazz
from src.tool import DateTime


def test_exchange_holidays():
    for exchange in config.EXCHANGES:
        result = tool.exchange_holidays(exchange)
        assert isinstance(result, set)


def test_last_workday():
    dt = DateTime(2020, 1, 21)
    assert tool.last_workday('NYSE', dt) == DateTime(2020, 1, 17)


def test_last_sunday():
    dt = DateTime(2020, 9, 1)
    assert tool.last_sunday(dt) == DateTime(2020, 8, 30)


def test_interval_name():
    assert tool.interval_name(tool.INTERVAL_1D) == '1d'


def test_time_slices_0():
    dt_from = DateTime(2020, 8, 28)
    dt_to = DateTime(2020, 8, 28, 10, 12, 10)
    slices = [(slice_from.format(), slice_to.format())
              for slice_from, slice_to in tool.time_slices(dt_from, dt_to, tool.INTERVAL_1D, 14)]
    assert slices == []


def test_time_slices_1():
    dt_from = DateTime(2020, 8, 28)
    dt_to = DateTime(2020, 8, 28, 10, 12, 10)
    slices = [(slice_from.format(), slice_to.format())
              for slice_from, slice_to in tool.time_slices(dt_from, dt_to, tool.INTERVAL_1H, 14)]
    assert slices == [('2020-08-28 01:00:00', '2020-08-28 10:12:10')]


def test_time_slices():
    dt_from = DateTime(2020, 2, 1)
    dt_to = DateTime(2020, 2, 4)
    slices = [(start.format(), stop.format())
              for start, stop in tool.time_slices(dt_from, dt_to, tool.INTERVAL_1H, 21)]
    assert slices == [
        ('2020-02-01 01:00:00', '2020-02-01 21:00:00'),
        ('2020-02-01 22:00:00', '2020-02-02 18:00:00'),
        ('2020-02-02 19:00:00', '2020-02-03 15:00:00'),
        ('2020-02-03 16:00:00', '2020-02-04 00:00:00')
    ]


def test_transpose():
    key, = tool.transpose([Clazz(key='v1'), Clazz(key='v2')], ['key'])
    assert key == ['v1', 'v2']


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
