from datetime import datetime, timezone
from typing import List, Any

from src import tools, exante, yahoo, stooq


def read_data_source(engine: Any) -> List:
    symbol = 'SIE.XETRA'
    interval = tools.INTERVAL_1D
    dt_from = datetime(2020, 8, 3, tzinfo=timezone.utc)
    dt_to = datetime(2020, 8, 11, tzinfo=timezone.utc)

    with engine.Session() as session:
        return session.series(symbol, dt_from, dt_to, interval)


def accept_price(v1: float, v2: float) -> bool:
    return 0.98 < v1 / v2 < 1.02


def accept_volume(v1: int, v2: int) -> bool:
    return 0.85 < v1 / v2 < 1.15


def test_session():
    data_exante = read_data_source(exante)
    data_yahoo = read_data_source(yahoo)
    data_stooq = read_data_source(stooq)

    for d_exante, d_yahoo, d_stooq in zip(data_exante, data_yahoo, data_stooq):
        assert d_exante['symbol'] == d_yahoo['symbol']
        assert d_yahoo['symbol'] == d_stooq['symbol']

        assert d_exante['timestamp'] == d_yahoo['timestamp']
        assert d_yahoo['timestamp'] == d_stooq['timestamp']

        assert accept_price(d_exante['open'], d_yahoo['open'])
        assert accept_price(d_yahoo['open'], d_stooq['open'])

        assert accept_price(d_exante['open'], d_yahoo['open'])
        assert accept_price(d_yahoo['open'], d_stooq['open'])

        assert accept_price(d_exante['low'], d_yahoo['low'])
        assert accept_price(d_yahoo['low'], d_stooq['low'])

        assert accept_price(d_exante['high'], d_yahoo['high'])
        assert accept_price(d_yahoo['high'], d_stooq['high'])

        assert accept_volume(d_exante['volume'], d_yahoo['volume'])
        assert accept_volume(d_yahoo['volume'], d_stooq['volume'])
