from datetime import datetime
from typing import List

from src import tools, exante, yahoo


def read_data_source(Session) -> List:
    symbol = 'XOM.NYSE'
    interval = tools.INTERVAL_1D
    dt_from = datetime(2020, 2, 2)
    dt_to = datetime(2020, 2, 4)

    with Session() as session:
        return session.series(symbol, dt_from, dt_to, interval)


def test_session():
    # TODO: fix the test
    data1 = read_data_source(exante.Session)
    data2 = read_data_source(yahoo.Session)
    assert data1 != data2
