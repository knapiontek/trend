from pprint import pprint

from src import store, config, session

URL = config.exante_url()
URL_EXCHANGES = f'{URL}/exchanges'
URL_ACCOUNTS = f'{URL}/accounts'


def display_resistance():
    with store.Store('resistance') as content:
        with session.ExanteSession() as exante:
            response = exante.get(url=URL_ACCOUNTS)
            assert response.status_code == 200, response.text

            accounts = response.json()
            content['accounts'] = accounts
            pprint(accounts)


if __name__ == '__main__':
    display_resistance()
