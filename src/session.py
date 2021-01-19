from datetime import datetime, timedelta
from typing import List

import requests

from src.clazz import Clazz


class Session(requests.Session):
    def __init__(self):
        super().__init__()

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Clazz]:
        raise NotImplementedError
