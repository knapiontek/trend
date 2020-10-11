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

from src import store, tools, yahoo, config, log, exante, stooq, analyse

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
GRAPH_MARGIN = {'l': 10, 'r': 10, 't': 35, 'b': 10, 'pad': 0}


def table_style(**kwargs):
    return dict(
        style_cell_conditional=[
            {
                'if': {'column_id': k},
                'textAlign': v,
            } for k, v in kwargs.items()
        ],
        style_header={'font-weight': 'bold', 'border-top': 'none'},
        style_cell={'padding': '5px'}
    )


exchange_choice = dcc.Dropdown(id='exchange-choice', placeholder='exchange', className='choice')
engine_choice = dcc.Dropdown(id='engine-choice', placeholder='engine', className='choice')

symbol_table = dash_table.DataTable(
    id='symbol-table',
    columns=[{'name': v, 'id': k} for k, v in SYMBOL_COLUMNS.items()],
    filter_action='custom',
    row_selectable='single',
    page_action='none',
    **table_style(symbol='left', shortable='center', health='center')
)

details_table = dash_table.DataTable(
    id='details-table',
    columns=[{'name': name, 'id': _id} for _id, name in (('key', 'Key'), ('value', 'Value'))],
    page_action='none',
    **table_style(key='left', value='right')
)

data_graph = dcc.Graph(id='data-graph', config={'scrollZoom': True}, className='panel')

app.layout = html.Div(
    [
        dcc.Store(id='nil-store', storage_type='local'),
        html.Div([
            html.Div([
                html.Div(exchange_choice, className='six columns'),
                html.Div(engine_choice, className='six columns')
            ], className='row', style={'height': '20'}),
            html.Div(symbol_table, className='scroll', style={'height': '60%'}),
            html.Div(details_table, className='scroll flex-element'),
        ], className='three columns panel flex-box'),
        html.Div([
            data_graph
        ], className='nine columns panel')
    ],
    className='row dashboard'
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


@app.callback([Output('exchange-choice', 'options'), Output('exchange-choice', 'value')],
              [Input('nil-store', 'data')])
def cb_exchange_choice(data):
    return [{'label': e, 'value': e} for e in config.ACTIVE_EXCHANGES], config.ACTIVE_EXCHANGES[0]


@app.callback([Output('engine-choice', 'options'), Output('engine-choice', 'value')],
              [Input('nil-store', 'data')])
def cb_engine_choice(data):
    engines = ['yahoo', 'stooq', 'exante']
    return [{'label': s, 'value': s} for s in engines], engines[0]


@app.callback(Output('symbol-table', 'data'),
              [Input('exchange-choice', 'value'),
               Input('engine-choice', 'value'),
               Input('symbol-table', 'filter_query')])
def cb_symbol_table(exchange_name, engine_name, filter_query):
    if exchange_name and engine_name:
        LOG.debug(f'Loading symbols with filter: "{filter_query or "*"}"')
        with store.Exchanges() as db_exchanges:
            instruments = db_exchanges[exchange_name]
        boolean = ['[-]', '[+]']
        instruments = [dict(i, shortable=boolean[i['shortable']], health=boolean[i[f'health-{engine_name}']])
                       for i in instruments]
        filtered = filter_instruments(instruments, filter_query)
        return list(tools.dict_it(filtered, SYMBOL_COLUMNS))
    return []


@app.callback(Output('data-graph', 'figure'),
              [Input('engine-choice', 'value'),
               Input('symbol-table', 'data'), Input('symbol-table', 'selected_rows')])
def cb_price_graph(engine_name, data, selected_rows):
    if engine_name and selected_rows:
        if data and selected_rows:
            row = data[selected_rows[0]]
            symbol = row['symbol']
            LOG.debug(f'Loading time series for symbol: {symbol}')
            engines = dict(yahoo=yahoo, exante=exante, stooq=stooq)
            engine = engines[engine_name]
            with engine.Series(tools.INTERVAL_1D) as db_series:
                time_series = db_series[symbol]

            zigzag = analyse.zigzag(time_series, 'close')
            params = tools.transpose(zigzag, ('timestamp', 'close', 'volume'))
            dates = [tools.from_timestamp(ts) for ts in params['timestamp']]

            prices = go.Scatter(x=dates, y=params['close'], name='Price', customdata=time_series, line=dict(width=1.5))
            volume = go.Bar(x=dates, y=params['volume'], name='Volume')
            figure = make_subplots(rows=2, cols=1,
                                   shared_xaxes=True,
                                   vertical_spacing=0.03,
                                   row_heights=[0.7, 0.3],
                                   specs=[[{'type': 'scatter'}], [{'type': 'bar'}]])
            figure.add_trace(prices, row=1, col=1)
            figure.add_trace(volume, row=2, col=1)
            figure.update_layout(margin=GRAPH_MARGIN, showlegend=False, title_text=symbol)
            return figure

    return go.Figure(data=[], layout=dict(margin=GRAPH_MARGIN))


@app.callback(
    Output('details-table', 'data'),
    [Input('data-graph', 'clickData')])
def cb_details_table(data):
    if data:
        points = data.get('points') or []
        return [{'key': k, 'value': v} for p in points for k, v in p.get('customdata').items()]
    return []


def run_dash(debug: bool):
    return app.run_server(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_dash(debug=debug)


if __name__ == '__main__':
    main()
