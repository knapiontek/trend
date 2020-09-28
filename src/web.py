import logging
import re
import sys
from typing import Dict, List

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go
from dash.dependencies import Output, Input
from plotly.subplots import make_subplots

from src import store, tools, style, yahoo, config, log

LOG = logging.getLogger(__name__)

app = dash.Dash(title='trend',
                url_base_pathname='/trend/',
                external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'],
                assets_folder=config.ASSETS_PATH)


def wsgi(environ, start_response):
    # gunicorn src.web:wsgi -b :8881
    return app.server(environ, start_response)


if 'gunicorn' in sys.modules:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.basicConfig(level=gunicorn_logger.level, handlers=gunicorn_logger.handlers)
    logging.getLogger('urllib3').setLevel(logging.INFO)

SYMBOL_COLUMNS = {'symbol': 'Symbol', 'shortable': 'Short', 'health': 'Health', 'total': 'Total'}
GRAPH_MARGIN = {'l': 15, 'r': 15, 't': 40, 'b': 15, 'pad': 4}

exchange_choice = dcc.Dropdown(id='exchange-choice', placeholder='exchange', className='choice')

symbol_table = dash_table.DataTable(
    id='symbol-table',
    columns=[{'name': v, 'id': k} for k, v in SYMBOL_COLUMNS.items()],
    filter_action='custom',
    row_selectable='single',
    page_action='none',
    sort_action='native',
    **style.symbol_table(symbol='left', shortable='center', health='center')
)

source_choice = dcc.Dropdown(id='source-choice', placeholder='source', className='choice')

data_graph = dcc.Graph(id='data-graph', config={'scrollZoom': True}, className='graph')

app.layout = html.Div(
    [
        dcc.Store(id='nil-store', storage_type='local'),
        html.Div([
            exchange_choice,
            html.Div(symbol_table, className='scroll')
        ], className='three columns panel'),
        html.Div([
            source_choice,
            data_graph
        ], className='nine columns panel')
    ],
    className='dashboard row'
)

PATTERN = re.compile('{(\\w+)} contains (.+)')


def filter_instruments(instruments: List[Dict], filter_query) -> List[Dict]:
    if filter_query:
        matches = [re.search(PATTERN, f) for f in filter_query.split(' && ')]
        if all(matches):
            # noinspection PyTypeChecker
            columns = dict([m.groups() for m in matches])
            # filter-phrase in value for all filter-columns
            return [
                i for i in instruments
                if all(v.lower() in str(i[k]).lower() for k, v in columns.items())
            ]
        else:
            return []
    else:
        return instruments


@app.callback(Output('exchange-choice', 'options'),
              [Input('nil-store', 'data')])
def cb_exchange_choice(data):
    return [{'label': e, 'value': e} for e in config.ACTIVE_EXCHANGES]


@app.callback(Output('symbol-table', 'data'),
              [Input('exchange-choice', 'value'),
               Input('symbol-table', 'filter_query')])
def cb_symbol_table(value, filter_query):
    LOG.debug(f'Loading symbols with filter: "{filter_query or "*"}"')
    with store.Exchanges() as db_exchanges:
        instruments = db_exchanges[value]
    filtered = filter_instruments(instruments, filter_query)
    return list(tools.dict_it(filtered, SYMBOL_COLUMNS))


@app.callback(Output('source-choice', 'options'),
              [Input('nil-store', 'data')])
def cb_source_choice(data):
    return [{'label': s, 'value': s} for s in ['yahoo', 'stooq', 'exante']]


@app.callback(Output('data-graph', 'figure'),
              [Input('source-choice', 'value'),
               Input('symbol-table', 'data'), Input('symbol-table', 'selected_rows')])
def cb_price_graph(value, data, selected_rows):
    if selected_rows:
        assert len(selected_rows) == 1
        row = data[selected_rows[0]]
        symbol = row['symbol']
        LOG.debug(f'Loading time series for symbol: {symbol}')
        with yahoo.Series(tools.INTERVAL_1D) as db_series:
            time_series = db_series[symbol]

        params = tools.transpose(time_series, ('timestamp', 'close', 'volume'))
        dates = [tools.from_timestamp(ts) for ts in params['timestamp']]

        prices = go.Scatter(x=dates, y=params['close'], name='Price', line=dict(width=1.5))
        volume = go.Bar(x=dates, y=params['volume'], name='Volume')
        figure = make_subplots(rows=2, cols=1,
                               shared_xaxes=True,
                               vertical_spacing=0.03,
                               row_heights=[0.7, 0.3],
                               specs=[[{'type': 'scatter'}], [{'type': 'bar'}]])
        figure.add_trace(prices, row=1, col=1)
        figure.add_trace(volume, row=2, col=1)
        figure.update_layout(margin=GRAPH_MARGIN, showlegend=False, title_text=symbol)
        figure.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
        return figure

    return go.Figure(data=[], layout=dict(margin=GRAPH_MARGIN))


def run_dash(debug: bool):
    return app.run_server(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_dash(debug=debug)


if __name__ == '__main__':
    main()
