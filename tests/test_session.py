from datetime import datetime
from typing import List, Type

from src import tools, exante, yahoo, session


def read_data_source(clazz: Type[session.Session]) -> List:
    symbol = 'XOM.NYSE'
    interval = tools.INTERVAL_1D
    dt_from = datetime(2020, 8, 3)
    dt_to = datetime(2020, 8, 11)

    with clazz() as _session:
        return _session.series(symbol, dt_from, dt_to, interval)


def accept_price(v1: float, v2: float) -> bool:
    return 0.98 < v1 / v2 < 1.02


def accept_volume(v1: int, v2: int) -> bool:
    return 0.85 < v1 / v2 < 1.15


def test_session():
    data_exante = read_data_source(exante.Session)
    data_yahoo = read_data_source(yahoo.Session)
    for d_exante, d_yahoo in zip(data_exante, data_yahoo):
        assert d_exante['symbol'] == d_yahoo['symbol']
        assert d_exante['timestamp'] == d_yahoo['timestamp']
        assert accept_price(d_exante['open'], d_yahoo['open'])
        assert accept_price(d_exante['close'], d_yahoo['close'])
        assert accept_price(d_exante['low'], d_yahoo['low'])
        assert accept_price(d_exante['high'], d_yahoo['high'])
        assert accept_volume(d_exante['volume'], d_yahoo['volume'])
