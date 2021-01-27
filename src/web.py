import logging
import re
import sys
from datetime import timedelta, datetime
from typing import Dict, List

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_table
import plotly.graph_objects as go
from dash.dependencies import Output, Input
from plotly.subplots import make_subplots

from src import config, log, tool, store, yahoo, exante, stooq, analyse
from src.tool import DateTime

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
SYMBOL_COLUMNS = dict(symbol='Symbol', shortable='Short', health='Health', profit_ratio='Profit %')
DATE_PICKER_FORMAT = 'YYYY-MM-DD'
XAXIS_FORMAT = '%Y-%m-%d'
GRAPH_MARGIN = {'l': 10, 'r': 10, 't': 35, 'b': 10, 'pad': 0}
SPIKE = {'spikemode': 'toaxis+across+marker', 'spikethickness': 1, 'spikecolor': 'black'}
PLOT_BGCOLOR = 'rgb(240,240,240)'
FLOAT_PRECISION = 4

exchange_choice = dcc.Dropdown(id='exchange-choice',
                               options=[{'label': e, 'value': e} for e in config.ACTIVE_EXCHANGES],
                               value=config.ACTIVE_EXCHANGES[0],
                               placeholder='exchange',
                               className='choice',
                               persistence=True)

engine_choice = dcc.Dropdown(id='engine-choice',
                             options=[{'label': s, 'value': s} for s in ENGINES],
                             value=list(ENGINES.keys())[0],
                             placeholder='engine',
                             className='choice',
                             persistence=True)

datetime_from = config.datetime_from() + timedelta(days=100)

date_choice = dcc.DatePickerSingle(id='date-from',
                                   date=datetime_from.date(),
                                   display_format=DATE_PICKER_FORMAT,
                                   className='choice',
                                   persistence=True)

score_choice = dcc.Input(id='score-choice',
                         type='number',
                         min=0, max=6, step=1, value=3.0,
                         className='score',
                         persistence=True)


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


security_table = dash_table.DataTable(
    id='security-table',
    columns=[{'name': v, 'id': k} for k, v in SYMBOL_COLUMNS.items()],
    filter_action='custom',
    row_selectable='single',
    page_action='none',
    **table_style(symbol='left', shortable='center', health='center')
)

details_table = dash_table.DataTable(
    id='details-table',
    columns=[{'name': name, 'id': _id}
             for _id, name in (('key', 'Key'), ('value', 'Value'))],
    page_action='none',
    **table_style(key='left', value='right')
)

action_table = dash_table.DataTable(
    id='action-table',
    columns=[{'name': name, 'id': _id}
             for _id, name in (('date', 'Date'), ('key', 'Key'), ('value', 'Value'))],
    page_action='none',
    **table_style(date='left', key='left', value='right')
)

series_graph = dcc.Graph(id='series-graph', config={'scrollZoom': True}, className='panel')

app.layout = dbc.Row(
    [
        dcc.Store(id='selected-security'),
        dbc.Col([
            dbc.Row([dbc.Col(exchange_choice), dbc.Col(engine_choice)], className='frame'),
            dbc.Row([dbc.Col(date_choice), dbc.Col(score_choice)], className='frame'),
            dbc.Row(dbc.Col(security_table), className='scroll', style={'max-height': '50%'}),
            dbc.Row(dbc.Col(details_table), className='scroll', style={'max-height': '20%'}),
            dbc.Row(dbc.Col(action_table), className='scroll flex-element'),
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


@app.callback(Output('security-table', 'data'),
              [Input('exchange-choice', 'value'),
               Input('engine-choice', 'value'),
               Input('security-table', 'filter_query')])
def cb_security_table(exchange_name, engine_name, query):
    if exchange_name and engine_name:
        LOG.debug(f'Loading symbols with query: "{query or "*"}"')
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]

        results = []
        boolean = ['[-]', '[+]']
        for security in securities:
            engine = security[engine_name]
            profit_ratio = engine.profit / engine.total if engine.total else 0.0
            results += [dict(symbol=security.symbol,
                             shortable=boolean[security.shortable],
                             health=boolean[engine.health],
                             profit_ratio=100 * round(profit_ratio, FLOAT_PRECISION),
                             description=security.description,
                             profit=round(engine.profit, FLOAT_PRECISION),
                             total=round(engine.total, FLOAT_PRECISION),
                             volume=round(engine.volume, FLOAT_PRECISION))]
        return select_securities(results, query)
    return []


@app.callback(Output('selected-security', 'data'),
              [Input('security-table', 'data'), Input('security-table', 'selected_rows')])
def cb_selected_security(data, selected_rows):
    if data and selected_rows and selected_rows[0] < len(data):
        return data[selected_rows[0]]
    return {}


@app.callback(Output('series-graph', 'figure'),
              [Input('date-from', 'date'),
               Input('engine-choice', 'value'),
               Input('score-choice', 'value'),
               Input('selected-security', 'data')])
def cb_series_graph(d_from, engine_name, score, selected_security):
    if engine_name is not None and d_from and selected_security:
        interval = tool.INTERVAL_1D
        symbol, description = selected_security['symbol'], selected_security['description']

        # engine series
        engine = ENGINES[engine_name]
        dt_from = DateTime.parse_date(d_from)
        with engine.SecuritySeries(interval, dt_from=dt_from) as security_series:
            time_series = security_series[symbol]

        if time_series:
            # customize data
            fields = ('timestamp', 'vma-100', 'profit', 'action', 'volume')
            ts, vma_100, profit, action, volume = tool.transpose(time_series, fields)
            daily_dates = [datetime.utcfromtimestamp(t) for t in ts]
            long = [a if a and a > 0 else None for a in action]
            short = [-a if a and a < 0 else None for a in action]
            fields = ('action', 'profit', 'timestamp', 'open_timestamp', 'open_position')
            action_custom = [{k: v for k, v in s.items() if k in fields} for s in time_series]

            reduced_series = analyse.reduce(time_series, score)
            ts, close = tool.transpose(reduced_series, ('timestamp', 'close'))
            reduced_dates = [datetime.utcfromtimestamp(t) for t in ts]
            fields = ('open', 'close', 'high', 'low', 'timestamp')
            reduced_custom = [{k: v for k, v in s.items() if k in fields} for s in reduced_series]

            # create traces
            reduced_trace = go.Scatter(x=reduced_dates, y=close, customdata=reduced_custom, name='Close', mode='lines',
                                       line=dict(width=1.5), connectgaps=True, marker=dict(color='blue'))
            vma_100_trace = go.Scatter(x=daily_dates, y=vma_100, name='VMA-100', mode='lines', line=dict(width=1.5),
                                       connectgaps=True, marker=dict(color='orange'))
            long_trace = go.Scatter(x=daily_dates, y=long, customdata=action_custom, name='Long', mode='markers',
                                    line=dict(width=1.5), connectgaps=True, marker=dict(color='green'))
            short_trace = go.Scatter(x=daily_dates, y=short, customdata=action_custom, name='Short', mode='markers',
                                     line=dict(width=1.5), connectgaps=True, marker=dict(color='red'))
            profit_trace = go.Scatter(x=daily_dates, y=profit, customdata=action_custom, name='Profit',
                                      mode='lines+markers', line=dict(width=1.5), connectgaps=True,
                                      marker=dict(color='blue'))
            volume_trace = go.Bar(x=daily_dates, y=volume, name='Volume', marker=dict(color='blue'))

            # create a graph
            figure = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                                   row_heights=[0.6, 0.2, 0.2])
            figure.add_trace(reduced_trace, row=1, col=1)
            figure.add_trace(vma_100_trace, row=1, col=1)
            figure.add_trace(long_trace, row=1, col=1)
            figure.add_trace(short_trace, row=1, col=1)
            figure.add_trace(profit_trace, row=2, col=1)
            figure.add_trace(volume_trace, row=3, col=1)
            figure.update_xaxes(tickformat=XAXIS_FORMAT)
            figure.update_layout(margin=GRAPH_MARGIN, showlegend=False, title_text=description, hovermode='closest',
                                 xaxis=SPIKE, yaxis=SPIKE, plot_bgcolor=PLOT_BGCOLOR)
            figure.update_xaxes(range=[daily_dates[0], daily_dates[-1]])
            return figure

    return go.Figure(data=[], layout=dict(margin=GRAPH_MARGIN, plot_bgcolor=PLOT_BGCOLOR))


@app.callback(
    Output('details-table', 'data'),
    [Input('selected-security', 'data')])
def cb_details_table(selected_security):
    results = [{'key': k, 'value': v} for k, v in selected_security.items()]
    return sorted(results, key=lambda d: d['key'])


@app.callback(
    Output('action-table', 'data'),
    [Input('series-graph', 'clickData')])
def cb_action_table(click_data):
    def convert_custom_data(datum: Dict) -> List[Dict]:
        date = DateTime.from_timestamp(datum['timestamp']).format()
        result = []
        for k, v in datum.items():
            if k == 'open_timestamp':
                result += [{'date': date, 'key': 'open-date', 'value': DateTime.from_timestamp(v).format()}]
            elif k == 'open_position':
                result += [{'date': date, 'key': 'open-position', 'value': round(v, FLOAT_PRECISION)}]
            elif k == 'timestamp':
                pass
            elif isinstance(v, float):
                result += [{'date': date, 'key': k, 'value': round(v, FLOAT_PRECISION)}]
            else:
                result += [{'date': date, 'key': k, 'value': v}]
        return result

    results = []
    if click_data:
        for p in click_data.get('points', []):
            cd = p.get('customdata')
            if cd:
                results += convert_custom_data(cd)
    return sorted(results, key=lambda d: (d['date'], d['key']))


def run_module(debug: bool):
    return app.run_server(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_module(debug=debug)


if __name__ == '__main__':
    main()
