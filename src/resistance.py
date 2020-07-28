from pprint import pprint

import requests

from src import store, config

URL = 'https://api-demo.exante.eu/md/2.0'
URL_EXCHANGES = f'{URL}/exchanges'
URL_ACCOUNTS = f'{URL}/accounts'


def display_resistance():
    with store.Store('resistance') as content:
        with requests.Session() as session:
            session.auth = config.exante()

            response = session.get(url=URL_ACCOUNTS)
            assert response.status_code == 200, response.text

            accounts = response.json()
            content['accounts'] = accounts
            pprint(accounts)


if __name__ == '__main__':
    display_resistance()
