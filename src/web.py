import logging
import re
import sys
from typing import Dict, List

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_table
import plotly.graph_objects as go
from dash.dependencies import Output, Input, State
from plotly.subplots import make_subplots

from src import config, log, tool, store, yahoo, exante, stooq

LOG = logging.getLogger(__name__)

app = dash.Dash(title='trend',
                url_base_pathname='/trend/',
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                assets_folder=config.ASSETS_PATH)


def wsgi(environ, start_response):
    # gunicorn src.web:wsgi -b :8881
    return app.server(environ, start_response)


if 'gunicorn' in sys.modules:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.basicConfig(level=gunicorn_logger.level, handlers=gunicorn_logger.handlers)
    logging.getLogger('urllib3').setLevel(logging.INFO)

ENGINES = dict(yahoo=yahoo, exante=exante, stooq=stooq)
SYMBOL_COLUMNS = dict(symbol='Symbol', shortable='Short', health='Health', total='Total')
DATE_PICKER_FORMAT = 'YYYY-MM-DD'
XAXIS_FORMAT = '%Y-%m-%d'
GRAPH_MARGIN = {'l': 10, 'r': 10, 't': 35, 'b': 10, 'pad': 0}
SPIKE = {'spikemode': 'toaxis+across+marker', 'spikethickness': 1, 'spikecolor': 'black'}

exchange_choice = dcc.Dropdown(id='exchange-choice',
                               options=[{'label': e, 'value': e} for e in config.ACTIVE_EXCHANGES],
                               value=config.ACTIVE_EXCHANGES[0],
                               placeholder='exchange', className='choice')

engine_choice = dcc.Dropdown(id='engine-choice',
                             options=[{'label': s, 'value': s} for s in ENGINES],
                             value=list(ENGINES.keys())[0],
                             placeholder='engine', className='choice')

date_choice = dcc.DatePickerSingle(id='date-from', date=config.datetime_from().date(),
                                   display_format=DATE_PICKER_FORMAT, className='choice')

grade_choice = dcc.Slider(id='grade-choice', min=0, max=config.max_grade(),
                          marks={i: f'Grade.{i}' for i in range(config.max_grade() + 1)}, value=1)


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

app.layout = dbc.Row(
    [
        dcc.Store(id='relayout-data', storage_type='session'),
        dbc.Col([
            dbc.Row([dbc.Col(date_choice), dbc.Col(exchange_choice), dbc.Col(engine_choice)], className='frame'),
            dbc.Row(dbc.Col(grade_choice), className='frame'),
            dbc.Row(dbc.Col(symbol_table), className='scroll', style={'max-height': '60%'}),
            dbc.Row(dbc.Col(details_table), className='scroll flex-element'),
        ], className='panel flex-box', width=3),
        dbc.Col(dbc.Spinner(series_graph))
    ],
    className='dashboard'
)

PATTERN = re.compile('{(\\w+)} contains (.+)')


def select_securities(securities: List[Dict], query) -> List[Dict]:
    if query:
        matches = [re.search(PATTERN, f) for f in query.split(' && ')]
        if all(matches):
            # noinspection PyTypeChecker
            columns = dict([m.groups() for m in matches])
            # select-phrase in value for all select-columns
            return [
                security for security in securities
                if all(v.lower() in str(security[k]).lower() for k, v in columns.items())
            ]
        else:
            return []
    else:
        return securities


@app.callback(Output('symbol-table', 'data'),
              [Input('exchange-choice', 'value'),
               Input('engine-choice', 'value'),
               Input('symbol-table', 'filter_query')])
def cb_symbol_table(exchange_name, engine_name, query):
    if exchange_name and engine_name:
        LOG.debug(f'Loading symbols with query: "{query or "*"}"')
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]
        boolean = ['[-]', '[+]']
        securities = [dict(security,
                           shortable=boolean[security.shortable],
                           health=boolean[security[f'health-{engine_name}']],
                           info=security.description)
                      for security in securities]
        return select_securities(securities, query)
    return []


@app.callback(Output('relayout-data', 'data'),
              [Input('series-graph', 'relayoutData')])
def cb_relayout_data(relayout_data):
    relayout_data = relayout_data or {}
    data = {}
    if {'xaxis.range[0]', 'xaxis.range[1]'} <= relayout_data.keys():
        data['xaxis'] = [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]
    if {'yaxis.range[0]', 'yaxis.range[1]'} <= relayout_data.keys():
        data['yaxis'] = [relayout_data['yaxis.range[0]'], relayout_data['yaxis.range[1]']]
    if {'yaxis2.range[0]', 'yaxis2.range[1]'} <= relayout_data.keys():
        data['yaxis2'] = [relayout_data['yaxis2.range[0]'], relayout_data['yaxis2.range[1]']]
    return data


@app.callback(Output('series-graph', 'figure'),
              [Input('date-from', 'date'),
               Input('engine-choice', 'value'),
               Input('grade-choice', 'value'),
               Input('symbol-table', 'data'), Input('symbol-table', 'selected_rows')],
              State('relayout-data', 'data'))
def cb_series_graph(d_from, engine_name, grade, data, selected_rows, relayout_data):
    if engine_name and d_from and data and selected_rows and selected_rows[0] < len(data):
        interval = tool.INTERVAL_1D
        row = data[selected_rows[0]]
        symbol, info = row['symbol'], row['info']

        # engine series
        engine = ENGINES[engine_name]
        dt_from = tool.d_parse(d_from)
        with engine.SecuritySeries(interval, dt_from=dt_from, grade=grade) as security_series:
            time_series = security_series[symbol]

        if time_series:
            # customize data
            trans = tool.transpose(time_series, ('timestamp', 'close', 'vma-50', 'volume'))
            dates = [tool.from_timestamp(ts) for ts in trans['timestamp']]
            custom = [s.to_dict() for s in time_series]

            # create traces
            close_trace = go.Scatter(x=dates, y=trans['close'], name='Close', customdata=custom, line=dict(width=1.5))
            vma_50_trace = go.Scatter(x=dates, y=trans['vma-50'], name='VMA-50', line=dict(width=1.5))
            volume_trace = go.Bar(x=dates, y=trans['volume'], name='Volume')

            # create a graph
            figure = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            figure.add_trace(close_trace, row=1, col=1)
            figure.add_trace(vma_50_trace, row=1, col=1)
            figure.add_trace(volume_trace, row=2, col=1)
            figure.update_xaxes(tickformat=XAXIS_FORMAT)
            figure.update_layout(margin=GRAPH_MARGIN, showlegend=False, title_text=info, hovermode='x',
                                 xaxis=SPIKE, yaxis=SPIKE)

            # clip data
            if 'xaxis' in relayout_data:
                figure.update_xaxes(range=relayout_data['xaxis'])
            if 'yaxis' in relayout_data:
                figure.update_yaxes(range=relayout_data['yaxis'], row=1, col=1)
            if 'yaxis2' in relayout_data:
                figure.update_yaxes(range=relayout_data['yaxis2'], row=2, col=1)

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


def run_module(debug: bool):
    return app.run_server(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_module(debug=debug)


if __name__ == '__main__':
    main()
