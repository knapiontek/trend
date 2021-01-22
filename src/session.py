from datetime import timedelta
from typing import List

import requests

from src.clazz import Clazz
from src.tool import DateTime


class Session(requests.Session):
    def __init__(self):
        super().__init__()

    def series(self, symbol: str, dt_from: DateTime, dt_to: DateTime, interval: timedelta) -> List[Clazz]:
        raise NotImplementedError
