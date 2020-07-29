import requests

from src import config


class ExanteSession(requests.Session):
    def __init__(self):
        requests.Session.__init__(self)
        self.auth = config.exante_auth()
