from pprint import pprint

import quandl

from src import config

quandl.ApiConfig.api_key = config.quandl_auth()

data = quandl.get('WSE/TSGAMES', start_date='2015-08-11', end_date='2020-08-13')
pprint(data)
