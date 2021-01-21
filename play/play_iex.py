from datetime import datetime

from iexfinance.stocks import get_historical_data

from src import config, store
from src.tool import DateTime

TOKEN = config.iex_auth()

start = DateTime(2019, 1, 1)
end = datetime.today()

stocks = ['AAPL', 'AMZN']
data = get_historical_data(stocks, start, end, token=TOKEN)

with store.File('iex_test', editable=True) as series:
    series.update(data)
