from datetime import datetime, timezone

from iexfinance.stocks import get_historical_data

from src import config, store

TOKEN = config.iex_auth()

start = datetime(2019, 1, 1, tzinfo=timezone.utc)
end = datetime.today()

stocks = ['AAPL', 'AMZN']
data = get_historical_data(stocks, start, end, token=TOKEN)

with store.FileStore('iex_test', editable=True) as series:
    series.update(data)
