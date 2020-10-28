from types import SimpleNamespace
from typing import List

from src import analyse

SERIES = [
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1514851200,
        'close': 1,
        'volume': 3
    },
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1514937600,
        'close': 2,
        'volume': 8
    },
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1515024000,
        'close': 3,
        'volume': 1
    },
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1515110400,
        'close': 4,
        'volume': 13
    },
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1515196800,
        'close': 5,
        'volume': 23
    },
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1515369600,
        'close': 4,
        'volume': 8
    },
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1515456000,
        'close': 3,
        'volume': 4
    },
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1515542400,
        'close': 4,
        'volume': 31
    },
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1515628800,
        'close': 5,
        'volume': 14
    },
    {
        'symbol': 'ABBV.NYSE',
        'timestamp': 1515715200,
        'close': 6,
        'volume': 15
    }
]


def series() -> List[SimpleNamespace]:
    return [SimpleNamespace(**s) for s in SERIES]


def test_simplify():
    key = 'close'
    series_close = [s[key] for s in SERIES]
    assert series_close == [1, 2, 3, 4, 5, 4, 3, 4, 5, 6]

    simplified = analyse.simplify(series(), key, 1)
    simplified_close = [s.__dict__[key] for s in simplified]
    assert simplified_close == [1, 5, 3, 6]


def test_sma():
    sma = analyse.sma(series(), 3)
    sma = [s.__dict__ for s in sma]
    assert sma == [{'timestamp': 1515196800, 'value': 3.0},
                   {'timestamp': 1515369600, 'value': 3.7777777777777772},
                   {'timestamp': 1515456000, 'value': 4.111111111111111},
                   {'timestamp': 1515542400, 'value': 3.9999999999999996},
                   {'timestamp': 1515628800, 'value': 3.888888888888889},
                   {'timestamp': 1515715200, 'value': 4.222222222222222}]


def test_vma():
    vma = analyse.vma(series(), 3)
    vma = [s.__dict__ for s in vma]
    assert vma == [{'timestamp': 1515196800, 'value': 3.2184002184002183},
                   {'timestamp': 1515369600, 'value': 4.114864864864864},
                   {'timestamp': 1515456000, 'value': 4.553393003393003},
                   {'timestamp': 1515542400, 'value': 4.3241870532568205},
                   {'timestamp': 1515628800, 'value': 4.21797183989875},
                   {'timestamp': 1515715200, 'value': 4.281463903390814}]
