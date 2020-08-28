import json
import logging
from datetime import datetime, timedelta

from src import store, session, log, tools, holidays

LOG = logging.getLogger(__name__)


def show_instrument_range():
    with store.DBSeries(tools.DURATION_1D) as series:
        time_range = series.time_range()
        print(json.dumps(time_range))


def update_series():
    log.init(__file__, persist=False)

    with store.FileStore('exchanges') as exchanges:
        instruments = sum([v for k, v in exchanges.items()], [])
    LOG.debug(f'loaded instruments: {len(instruments)}')
    symbols = [i['symbolId'] for i in instruments][:10]

    duration = tools.DURATION_1D
    slice_delta = timedelta(seconds=1000 * duration)
    time_delta = timedelta(seconds=duration)
    dt_from_default = datetime(2017, 12, 31, tzinfo=tools.UTC_TZ)
    dt_to = tools.dt_truncate(datetime.now(tz=tools.UTC_TZ), duration)

    with store.DBSeries(duration) as series:
        time_range = series.time_range()
    LOG.debug(f'loaded time-range entries: {len(time_range)}')

    latest = {r['symbol']: tools.dt_parse(r['max_utc']) for r in time_range}
    instruments_latest = {s: latest.get(s) or dt_from_default for s in symbols}

    with session.ExanteSession() as exante:
        for symbol, dt_from in instruments_latest.items():
            for slice_from, slice_to in tools.time_slices(dt_from, dt_to, slice_delta, time_delta):
                time_series = exante.series(symbol, slice_from, slice_to, duration)

                with store.DBSeries(duration, editable=True) as db_series:
                    db_series += time_series


def verify_instrument(symbol: str, exchange: str):
    LOG.debug(f'testing instrument: {symbol}')

    duration = tools.DURATION_1D
    dt_from = datetime(2018, 1, 1, tzinfo=tools.UTC_TZ)
    dt_to = tools.dt_truncate(datetime.now(tz=tools.UTC_TZ), duration)
    time_delta = timedelta(seconds=duration)

    with store.DBSeries(duration) as db_series:
        series = db_series[symbol]

    series_days = {daily['utc'] for daily in series}
    assert not series_days & holidays.HOLIDAYS[exchange]
    all_days = series_days | holidays.HOLIDAYS[exchange]

    start = dt_from
    while start < dt_to:
        if start.weekday() in (0, 1, 2, 3, 4):
            day = tools.dt_format(dt_from)
            if day not in all_days:
                print(f'Missing: {day} for {symbol}')
        start += time_delta


def verify_series():
    log.init(__file__, persist=False)

    with store.FileStore('exchanges') as exchanges:
        instruments = sum([v for k, v in exchanges.items()], [])
    LOG.debug(f'loaded instruments: {len(instruments)}')
    for instrument in instruments:
        verify_instrument(instrument['symbolId'], instrument['exchange'])


def reload_exchanges():
    with store.FileStore('exchanges', editable=True) as content:
        with session.ExanteSession() as exante:
            for exchange in ['NYSE', 'NASDAQ']:
                symbols = exante.symbols(exchange)
                content[exchange] = symbols


if __name__ == '__main__':
    # update_series()
    verify_series()
