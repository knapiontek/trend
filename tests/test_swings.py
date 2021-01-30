import orjson as json

from src import swings, config
from src.clazz import Clazz

SERIES = [
    Clazz(symbol='XOM.NYSE', timestamp=1514851200, open=1.0, close=1.0, low=1.0, high=1.0, volume=3),
    Clazz(symbol='XOM.NYSE', timestamp=1514937600, open=2.0, close=2.0, low=2.0, high=2.0, volume=8),
    Clazz(symbol='XOM.NYSE', timestamp=1515024000, open=3.0, close=3.0, low=3.0, high=3.0, volume=1),
    Clazz(symbol='XOM.NYSE', timestamp=1515110400, open=4.0, close=4.0, low=4.0, high=4.0, volume=13),
    Clazz(symbol='XOM.NYSE', timestamp=1515196800, open=5.0, close=5.0, low=5.0, high=5.0, volume=23),
    Clazz(symbol='XOM.NYSE', timestamp=1515369600, open=4.0, close=4.0, low=4.0, high=4.0, volume=8),
    Clazz(symbol='XOM.NYSE', timestamp=1515456000, open=3.0, close=3.0, low=3.0, high=3.0, volume=4),
    Clazz(symbol='XOM.NYSE', timestamp=1515542400, open=4.0, close=4.0, low=4.0, high=4.0, volume=31),
    Clazz(symbol='XOM.NYSE', timestamp=1515628800, open=5.0, close=5.0, low=5.0, high=5.0, volume=14),
    Clazz(symbol='XOM.NYSE', timestamp=1515715200, open=6.0, close=6.0, low=6.0, high=6.0, volume=15)
]


def test_data():
    assert [s.close for s in SERIES] == [1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 4.0, 5.0, 6.0]


def test_reduce_1():
    score = 1
    reduced = swings.init(SERIES)
    reduced = swings.reduce(reduced, score)
    assert [s.value for s in swings.display(reduced, score)] == [1.0, 5.0, 3.0, 6.0]


def test_reduce_4():
    with config.TESTS_PATH.joinpath('sample.json').open() as sample_io:
        sample = json.loads(sample_io.read())
        security = [Clazz(s) for s in sample['KGH.WSE']]

    score = 4
    reduced = swings.init(security)
    reduced = swings.reduce(reduced, score)
    assert len(reduced) == 72
