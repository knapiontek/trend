import csv
import logging
import re
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import List, Dict, Optional

from src import tool, store, session, config, flow
from src.calendar import Calendar
from src.clazz import Clazz

LOG = logging.getLogger(__name__)

DT_FORMAT = '%Y-%m-%d'
QUOTE_URL = 'https://finance.yahoo.com/quote'
SYMBOL_URL = 'https://query1.finance.yahoo.com/v7/finance/download/{symbol}'
PATTERN = re.compile('"CrumbStore":{"crumb":"(.+?)"}')


def interval_to_yahoo(interval: timedelta):
    return {
        tool.INTERVAL_1D: '1d',
        tool.INTERVAL_1W: '1wk'
    }[interval]


def timestamp_from_yahoo(date: str) -> int:
    dt = datetime.strptime(date, DT_FORMAT)
    return Calendar.to_timestamp(dt.replace(tzinfo=timezone.utc))


def datum_from_yahoo(dt: Dict, symbol: str) -> Optional[Clazz]:
    try:
        return Clazz(symbol=symbol,
                     timestamp=timestamp_from_yahoo(dt['Date']),
                     open=float(dt['Open']),
                     close=float(dt['Close']),
                     low=float(dt['Low']),
                     high=float(dt['High']),
                     volume=int(dt['Volume']))
    except:
        return None


class Session(session.Session):
    def __enter__(self) -> 'Session':
        response = self.get(QUOTE_URL)
        assert response.status_code == 200, f'url: {QUOTE_URL} reply: {response.text}'
        found = re.search(PATTERN, response.text)
        if not found:
            raise RuntimeError(f'Expected response from the yahoo api: {PATTERN.pattern}')
        self.crumb = found.group(1)
        return self

    def series(self, symbol: str, dt_from: datetime, dt_to: datetime, interval: timedelta) -> List[Clazz]:
        short_symbol, exchange = tool.symbol_split(symbol)
        if exchange not in ('NYSE', 'NASDAQ'):
            return []

        flow.wait(max(0.6 - config.loop_delay(), 0))  # sleep at least 0.6 including loop in the flow module

        yahoo_symbol = short_symbol.replace('.', '-')
        yahoo_from = Calendar.to_timestamp(dt_from)
        yahoo_to = Calendar.to_timestamp(dt_to + interval)
        yahoo_interval = interval_to_yahoo(interval)

        url = SYMBOL_URL.format(symbol=yahoo_symbol)
        params = dict(period1=yahoo_from, period2=yahoo_to, interval=yahoo_interval, events='history', crumb=self.crumb)
        response = self.get(url, params=params)
        if response.status_code in (400, 404):
            return []
        assert response.status_code == 200, f'url: {url} params: {params} reply: {response.text}'
        data = [datum_from_yahoo(item, symbol) for item in csv.DictReader(StringIO(response.text))]
        if len(data) == 2 and data[0].timestamp == data[1].timestamp:
            data = data[0:1]  # if yahoo returns 2 rows with duplicated values
        data = [
            datum
            for datum in data
            if datum and yahoo_from <= datum.timestamp <= yahoo_to
        ]
        return data


class SecuritySeries(store.SecuritySeries):
    def __init__(self, interval: timedelta, editable=False, dt_from: datetime = None):
        name = f'security_{tool.module_name(__name__)}_{tool.interval_name(interval)}'
        super().__init__(name, editable, dt_from)
