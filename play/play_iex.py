from pprint import pprint

import requests

from src import config

TOKEN = config.iex_auth()
URL = f'https://cloud.iexapis.com/stable/ref-data/exchanges?token={TOKEN}'

response = requests.get(URL)
pprint(response.json())
