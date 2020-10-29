from src import analyse, tool

SERIES = [
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1514851200,
               open=1.0, close=1.0, low=1.0, high=1.0, volume=3, sma=0.0, vma=0.0, order=0),
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1514937600,
               open=1.0, close=2.0, low=1.0, high=1.0, volume=8, sma=0.0, vma=0.0, order=0),
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1515024000,
               open=1.0, close=3.0, low=1.0, high=1.0, volume=1, sma=0.0, vma=0.0, order=0),
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1515110400,
               open=1.0, close=4.0, low=1.0, high=1.0, volume=13, sma=0.0, vma=0.0, order=0),
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1515196800,
               open=1.0, close=5.0, low=1.0, high=1.0, volume=23, sma=0.0, vma=0.0, order=0),
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1515369600,
               open=1.0, close=4.0, low=1.0, high=1.0, volume=8, sma=0.0, vma=0.0, order=0),
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1515456000,
               open=1.0, close=3.0, low=1.0, high=1.0, volume=4, sma=0.0, vma=0.0, order=0),
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1515542400,
               open=1.0, close=4.0, low=1.0, high=1.0, volume=31, sma=0.0, vma=0.0, order=0),
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1515628800,
               open=1.0, close=5.0, low=1.0, high=1.0, volume=14, sma=0.0, vma=0.0, order=0),
    tool.Clazz(symbol='XOM.NYSE',
               timestamp=1515715200,
               open=1.0, close=6.0, low=1.0, high=1.0, volume=15, sma=0.0, vma=0.0, order=0)
]


def test_simplify():
    series_close = [s.close for s in SERIES]
    assert series_close == [1, 2, 3, 4, 5, 4, 3, 4, 5, 6]

    simplified = analyse.simplify(SERIES, 1)
    simplified_close = [s.close for s in simplified]
    assert simplified_close == [1, 5, 3, 6]


def test_sma():
    sma = analyse.sma(SERIES, 3)
    assert sma == [{'timestamp': 1515196800, 'value': 3.0},
                   {'timestamp': 1515369600, 'value': 3.7777777777777772},
                   {'timestamp': 1515456000, 'value': 4.111111111111111},
                   {'timestamp': 1515542400, 'value': 3.9999999999999996},
                   {'timestamp': 1515628800, 'value': 3.888888888888889},
                   {'timestamp': 1515715200, 'value': 4.222222222222222}]


def test_vma():
    vma = analyse.vma(SERIES, 3)
    assert vma == [{'timestamp': 1515196800, 'value': 3.2184002184002183},
                   {'timestamp': 1515369600, 'value': 4.114864864864864},
                   {'timestamp': 1515456000, 'value': 4.553393003393003},
                   {'timestamp': 1515542400, 'value': 4.3241870532568205},
                   {'timestamp': 1515628800, 'value': 4.21797183989875},
                   {'timestamp': 1515715200, 'value': 4.281463903390814}]
