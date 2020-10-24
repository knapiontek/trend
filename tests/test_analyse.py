from src import analyse

SERIES = [
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1514851200,
        "close": 1,
    },
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1514937600,
        "close": 2,
    },
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1515024000,
        "close": 3,
    },
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1515110400,
        "close": 4,
    },
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1515196800,
        "close": 5,
    },
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1515369600,
        "close": 4,
    },
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1515456000,
        "close": 3,
    },
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1515542400,
        "close": 4,
    },
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1515628800,
        "close": 5,
    },
    {
        "symbol": "ABBV.NYSE",
        "timestamp": 1515715200,
        "close": 6,
    }
]


def test_simplify():
    key = 'close'
    series_close = [s[key] for s in SERIES]
    assert series_close == [1, 2, 3, 4, 5, 4, 3, 4, 5, 6]

    simplified = analyse.simplify(SERIES, key, 1)
    simplified_close = [s[key] for s in simplified]
    assert simplified_close == [1, 5, 3, 6]
