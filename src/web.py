import logging
import re
import sys
from datetime import timedelta
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

OPTIONS = dict(simplified='Simplified', close='Close')
ENGINES = dict(yahoo=yahoo, exante=exante, stooq=stooq)
SYMBOL_COLUMNS = dict(symbol='Symbol', shortable='Short', health='Health', total='Total')
GRAPH_MARGIN = {'l': 10, 'r': 10, 't': 35, 'b': 10, 'pad': 0}

exchange_choice = dcc.Dropdown(id='exchange-choice',
                               options=[{'label': e, 'value': e} for e in config.ACTIVE_EXCHANGES],
                               value=config.ACTIVE_EXCHANGES[0],
                               placeholder='exchange', className='choice')

engine_choice = dcc.Dropdown(id='engine-choice',
                             options=[{'label': s, 'value': s} for s in ENGINES],
                             value=list(ENGINES.keys())[0],
                             placeholder='engine', className='choice')

options_choice = dcc.Checklist(id='options-choice',
                               options=[{'label': v, 'value': k} for k, v in OPTIONS.items()],
                               labelStyle={'display': 'inline'},
                               value=[list(OPTIONS.keys())[0]],
                               style={'padding': 10})


def table_style(**kwargs):
    return dict(
        style_cell_conditional=[
            {
                'if': {'column_id': k},
                'textAlign': v,
            } for k, v in kwargs.items()
        ],
        style_header={'font-weight': 'bold'},
        style_cell={'padding': 5}
    )


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

series_graph = dcc.Graph(id='series-graph', config={'scrollZoom': True}, className='panel')

app.layout = html.Div(
    [
        html.Div([
            html.Div([
                html.Div(exchange_choice, className='six columns'),
                html.Div(engine_choice, className='six columns')
            ], className='row frame'),
            html.Div(options_choice, className='frame'),
            html.Div(symbol_table, className='scroll', style={'max-height': '60%'}),
            html.Div(details_table, className='scroll flex-element'),
        ], className='three columns panel flex-box'),
        html.Div(series_graph, className='nine columns panel')
    ],
    className='row dashboard'
)

PATTERN = re.compile('{(\\w+)} contains (.+)')


def select_instruments(instruments: List[Dict], query) -> List[Dict]:
    if query:
        matches = [re.search(PATTERN, f) for f in query.split(' && ')]
        if all(matches):
            # noinspection PyTypeChecker
            columns = dict([m.groups() for m in matches])
            # select-phrase in value for all select-columns
            return [
                i for i in instruments
                if all(v.lower() in str(i[k]).lower() for k, v in columns.items())
            ]
        else:
            return []
    else:
        return instruments


@app.callback(Output('symbol-table', 'data'),
              [Input('exchange-choice', 'value'),
               Input('engine-choice', 'value'),
               Input('symbol-table', 'filter_query')])
def cb_symbol_table(exchange_name, engine_name, query):
    if exchange_name and engine_name:
        LOG.debug(f'Loading symbols with query: "{query or "*"}"')
        with store.Exchanges() as db_exchanges:
            instruments = db_exchanges[exchange_name]
        boolean = ['[-]', '[+]']
        instruments = [dict(i,
                            shortable=boolean[i['shortable']],
                            health=boolean[i[f'health-{engine_name}']],
                            info=i['description'])
                       for i in instruments]
        return select_instruments(instruments, query)
    return []


@app.callback(Output('series-graph', 'figure'),
              [Input('engine-choice', 'value'),
               Input('options-choice', 'value'),
               Input('symbol-table', 'data'), Input('symbol-table', 'selected_rows')])
def cb_series_graph(engine_name, options, data, selected_rows):
    if engine_name and selected_rows:
        if data and selected_rows:
            row = data[selected_rows[0]]
            symbol, info = row['symbol'], row['info']

            LOG.debug(f'Loading time series for symbol: {symbol}')
            dt_from = tools.utc_now() - timedelta(days=1400)
            engine = ENGINES[engine_name]
            with engine.Series(tools.INTERVAL_1D) as db_series:
                time_series = [s for s in db_series[symbol] if tools.from_timestamp(s['timestamp']) > dt_from]

            figure = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

            if 'simplified' in options:
                simplified = analyse.simplify(time_series, 'close')
                params = tools.transpose(simplified, ('timestamp', 'close', 'volume'))
                dates = [tools.from_timestamp(ts) for ts in params['timestamp']]
                closes = go.Scatter(x=dates, y=params['close'],
                                    name='Simplified', customdata=time_series, line=dict(width=1.5))
                figure.add_trace(closes, row=1, col=1)
                volume = go.Bar(x=dates, y=params['volume'], name='Volume')
                figure.add_trace(volume, row=2, col=1)

            if 'close' in options:
                params = tools.transpose(time_series, ('timestamp', 'close', 'volume'))
                dates = [tools.from_timestamp(ts) for ts in params['timestamp']]
                closes = go.Scatter(x=dates, y=params['close'],
                                    name='Close', customdata=time_series, line=dict(width=1.5))
                figure.add_trace(closes, row=1, col=1)
                volume = go.Bar(x=dates, y=params['volume'], name='Volume')
                figure.add_trace(volume, row=2, col=1)

            figure.update_layout(margin=GRAPH_MARGIN,
                                 showlegend=False,
                                 title_text=info)
            return figure

    return go.Figure(data=[], layout=dict(margin=GRAPH_MARGIN))


@app.callback(
    Output('details-table', 'data'),
    [Input('series-graph', 'clickData')])
def cb_details_table(data):
    if data:
        points = data.get('points') or []
        return [{'key': k, 'value': v} for p in points for k, v in p.get('customdata', {}).items()]
    return []


def run_dash(debug: bool):
    return app.run_server(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_dash(debug=debug)


if __name__ == '__main__':
    main()
