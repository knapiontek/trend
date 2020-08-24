from datetime import datetime, timedelta
from pprint import pprint

from src import store, session, log, config, tools


def show_symbol_range():
    with store.DBSeries(config.DURATION_1D) as series:
        time_range = series.time_range()
        pprint(time_range, width=120)


def reload_price_history(symbol: str):
    dt_from = datetime(2020, 1, 1, tzinfo=config.UTC_TZ)
    dt_to = datetime.now(tz=config.UTC_TZ)

    with session.ExanteSession() as exante:
        time_series = exante.series(symbol, dt_from, dt_to, config.DURATION_1D)

        with store.DBSeries(config.DURATION_1D) as db_series:
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

    duration = config.DURATION_1D
    delta = timedelta(days=30)
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

                with store.DBSeries(duration) as db_series:
                    db_series += time_series


def reload_exchanges():
    with store.FileStore('exchanges') as content:
        with session.ExanteSession() as exante:
            for exchange in ['NYSE', 'NASDAQ']:
                symbols = exante.symbols(exchange)
                content[exchange] = symbols


if __name__ == '__main__':
    update_series()
