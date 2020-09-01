from yahoofinancials import YahooFinancials

from src import store

assets = ['TSLA', 'MSFT', 'FB']

yahoo = YahooFinancials(assets)

data = yahoo.get_historical_price_data(start_date='2019-01-01', end_date='2020-09-01', time_interval='weekly')

with store.FileStore('yahoo_test', editable=True) as series:
    series.update(data)
