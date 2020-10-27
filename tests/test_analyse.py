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


def test_simplify():
    key = 'close'
    series_close = [s[key] for s in SERIES]
    assert series_close == [1, 2, 3, 4, 5, 4, 3, 4, 5, 6]

    simplified = analyse.simplify(SERIES, key, 1)
    simplified_close = [s[key] for s in simplified]
    assert simplified_close == [1, 5, 3, 6]


def test_sma():
    sma = analyse.sma(SERIES, 3)
    assert sma == [{'sma': 2.0, 'timestamp': 1515024000},
                   {'sma': 3.0, 'timestamp': 1515110400},
                   {'sma': 4.0, 'timestamp': 1515196800},
                   {'sma': 4.333333333333333, 'timestamp': 1515369600},
                   {'sma': 4.0, 'timestamp': 1515456000},
                   {'sma': 3.6666666666666665, 'timestamp': 1515542400},
                   {'sma': 4.0, 'timestamp': 1515628800},
                   {'sma': 5.0, 'timestamp': 1515715200}]


def test_vma():
    vma = analyse.vma(SERIES, 3)
    assert vma == [{'timestamp': 1515024000, 'vma': 1.8333333333333333},
                   {'timestamp': 1515110400, 'vma': 3.227272727272727},
                   {'timestamp': 1515196800, 'vma': 4.594594594594595},
                   {'timestamp': 1515369600, 'vma': 4.5227272727272725},
                   {'timestamp': 1515456000, 'vma': 4.542857142857143},
                   {'timestamp': 1515542400, 'vma': 3.9069767441860463},
                   {'timestamp': 1515628800, 'vma': 4.204081632653061},
                   {'timestamp': 1515715200, 'vma': 4.733333333333333}]
