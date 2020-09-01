from datetime import datetime, timedelta
from typing import List

from yahoofinancials import YahooFinancials


class Session:
    def __init__(self):
        pass

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List:
        pass


def main():
    from src import store
    assets = ['TSLA', 'MSFT', 'FB']

    yahoo = YahooFinancials(assets)

    data = yahoo.get_historical_price_data(start_date='2019-01-01', end_date='2020-09-01', time_interval='weekly')

    with store.FileStore('yahoo_test', editable=True) as series:
        series.update(data)


if __name__ == '__main__':
    main()
