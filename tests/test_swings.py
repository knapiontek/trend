import orjson as json

from src import swings, config
from src.clazz import Clazz

SERIES = [
    Clazz(symbol='XOM.NYSE', timestamp=1514851200, open=1.0, close=1.0, low=1.0, high=1.0, volume=3),
    Clazz(symbol='XOM.NYSE', timestamp=1514937600, open=1.0, close=2.0, low=1.0, high=1.0, volume=8),
    Clazz(symbol='XOM.NYSE', timestamp=1515024000, open=1.0, close=3.0, low=1.0, high=1.0, volume=1),
    Clazz(symbol='XOM.NYSE', timestamp=1515110400, open=1.0, close=4.0, low=1.0, high=1.0, volume=13),
    Clazz(symbol='XOM.NYSE', timestamp=1515196800, open=1.0, close=5.0, low=1.0, high=1.0, volume=23),
    Clazz(symbol='XOM.NYSE', timestamp=1515369600, open=1.0, close=4.0, low=1.0, high=1.0, volume=8),
    Clazz(symbol='XOM.NYSE', timestamp=1515456000, open=1.0, close=3.0, low=1.0, high=1.0, volume=4),
    Clazz(symbol='XOM.NYSE', timestamp=1515542400, open=1.0, close=4.0, low=1.0, high=1.0, volume=31),
    Clazz(symbol='XOM.NYSE', timestamp=1515628800, open=1.0, close=5.0, low=1.0, high=1.0, volume=14),
    Clazz(symbol='XOM.NYSE', timestamp=1515715200, open=1.0, close=6.0, low=1.0, high=1.0, volume=15)
]


def test_data():
    assert [s.close for s in SERIES] == [1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 4.0, 5.0, 6.0]


def test_reduce_1():
    series = [Clazz(s, value=s['close']) for s in SERIES]
    swings.init(series)
    reduced = swings.reduce(series, 1)
    assert [s.value for s in reduced] == [1.0, 5.0, 3.0, 6.0]


def test_reduce_4():
    with config.TESTS_PATH.joinpath('sample.json').open() as sample_io:
        sample = json.loads(sample_io.read())
        security = [Clazz(s) for s in sample['KGH.WSE']]

    security = [Clazz(s, value=s['close']) for s in security]
    swings.init(security)
    reduced = swings.reduce(security, 4)
    assert len(reduced) == 43
