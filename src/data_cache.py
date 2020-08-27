from datetime import datetime, timedelta
from pprint import pprint

from src import store, session, log, config, tools, holidays


def show_symbol_range():
    with store.DBSeries(config.DURATION_1D) as series:
        time_range = series.time_range()
        pprint(time_range, width=120)


def reload_price_history(symbol: str):
    dt_from = datetime(2020, 1, 1, tzinfo=config.UTC_TZ)
    dt_to = datetime.now(tz=config.UTC_TZ)

    with session.ExanteSession() as exante:
        time_series = exante.series(symbol, dt_from, dt_to, config.DURATION_1D)

        with store.DBSeries(config.DURATION_1D, editable=True) as db_series:
            db_series += time_series


def update_series():
    log.init(__file__, persist=False)

    symbols = {'EUR/USD.E.FX',
               'EUR/GBP.E.FX',
               'XAG/USD.E.FX',
               'PKO.WSE',
               'KRU.WSE',
               'CDR.WSE',
               'XOM.NYSE',
               'TSLA.NASDAQ'}

    with store.FileStore('exchanges') as content:
        data = content['NASDAQ']
    symbols = [d['symbolId'] for d in data]

    duration = config.DURATION_1D
    delta = timedelta(days=1000)
    dt_from_default = datetime(2018, 1, 1, tzinfo=config.UTC_TZ)
    dt_to = datetime.now(tz=config.UTC_TZ)

    with store.DBSeries(duration) as series:
        time_range = series.time_range()

    latest = {r['symbol']: tools.dt_parse(r['max_utc']) + config.duration_delta(duration) for r in time_range}
    symbols_latest = {s: latest.get(s) or dt_from_default for s in symbols}

    with session.ExanteSession() as exante:
        for symbol, dt_from in symbols_latest.items():
            for slice_from, slice_to in tools.time_slices(dt_from, dt_to, delta, duration):
                time_series = exante.series(symbol, slice_from, slice_to, duration)

                with store.DBSeries(duration, editable=True) as db_series:
                    db_series += time_series


def verify_series():
    nyse = 'NYSE'
    nasdaq = 'NASDAQ'
    duration = config.DURATION_1D
    delta = timedelta(days=1)
    dt_from = datetime(2018, 1, 1, tzinfo=config.UTC_TZ)
    dt_to = datetime.now(tz=config.UTC_TZ)

    with store.DBSeries(duration) as series:
        xom = series['XOM.NYSE']
        tesla = series['TSLA.NASDAQ']

    xom_utc_days = {daily['utc'] for daily in xom}
    tesla_utc_days = {daily['utc'] for daily in tesla}

    assert not xom_utc_days & holidays.HOLIDAYS[nyse]
    assert not tesla_utc_days & holidays.HOLIDAYS[nasdaq]

    daily_nyse = xom_utc_days | holidays.HOLIDAYS[nyse]
    daily_nasdaq = tesla_utc_days | holidays.HOLIDAYS[nasdaq]

    while dt_from < dt_to:
        if dt_from.weekday() in (0, 1, 2, 3, 4):
            formatted = tools.dt_format(dt_from)
            if formatted not in daily_nyse:
                print(f'NYSE: {formatted}')
            if formatted not in daily_nasdaq:
                print(f'NASDAQ: {formatted}')
        dt_from += delta


def reload_exchanges():
    with store.FileStore('exchanges', editable=True) as content:
        with session.ExanteSession() as exante:
            for exchange in ['NYSE', 'NASDAQ']:
                symbols = exante.symbols(exchange)
                content[exchange] = symbols


if __name__ == '__main__':
    update_series()
    # verify_series()
