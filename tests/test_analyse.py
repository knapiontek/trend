from src import analyse, tool, yahoo, swings
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


def test_clean():
    extra = [Clazz(s, extra=1) for s in SERIES]
    analyse.clean(extra)
    assert extra == SERIES


def test_sma():
    series = SERIES[:]
    analyse.sma(series, 3)
    sma = [(s.timestamp, s['sma-3']) for s in series if 'sma-3' in s]
    assert sma == [(1515024000, 2.0),
                   (1515110400, 3.0),
                   (1515196800, 4.0),
                   (1515369600, 4.333333333333333),
                   (1515456000, 4.0),
                   (1515542400, 3.6666666666666665),
                   (1515628800, 4.0),
                   (1515715200, 5.0)]


def test_vma():
    series = SERIES[:]
    analyse.vma(series, 3)
    vma = [(s.timestamp, s['vma-3']) for s in series if 'vma-3' in s]
    assert vma == [(1515024000, 1.8333333333333333),
                   (1515110400, 3.227272727272727),
                   (1515196800, 4.594594594594595),
                   (1515369600, 4.5227272727272725),
                   (1515456000, 4.542857142857143),
                   (1515542400, 3.9069767441860463),
                   (1515628800, 4.204081632653061),
                   (1515715200, 4.733333333333333)]


def test_action():
    symbol = 'XOM.NYSE'
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        time_series = security_series[symbol]

    time_series = [Clazz(s, value=s['close']) for s in time_series]
    swings.init(time_series)
    swings.reduce(time_series, 3)
    analyse.action(time_series)
