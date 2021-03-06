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
from dash.dependencies import Output, Input, State
from plotly.subplots import make_subplots

from src import config, log, tool, store, yahoo, exante, stooq, swings
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
SPIKE = dict(spikemode='toaxis+across+marker', spikethickness=1, spikecolor='black')
LEGEND = dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
PLOT_BGCOLOR = 'rgb(240,240,240)'
FLOAT_PRECISION = 4

# TODO: support live
env_choice = dcc.Dropdown(id='env-choice',
                          options=[{'label': 'Test', 'value': tool.ENV_TEST}],
                          value=config.EXCHANGES[0],
                          placeholder='env',
                          className='choice',
                          persistence=True)

# TODO: support 1h
interval_choice = dcc.Dropdown(id='interval-choice',
                               options=[{'label': 'Interval 1D', 'value': tool.INTERVAL_1D_NAME}],
                               value=config.EXCHANGES[0],
                               placeholder='interval',
                               className='choice',
                               persistence=True)

exchange_choice = dcc.Dropdown(id='exchange-choice',
                               options=[{'label': e, 'value': e} for e in config.EXCHANGES],
                               value=config.EXCHANGES[0],
                               placeholder='exchange',
                               className='choice',
                               persistence=True)

engine_choice = dcc.Dropdown(id='engine-choice',
                             options=[{'label': s, 'value': s} for s in ENGINES],
                             value=list(ENGINES.keys())[0],
                             placeholder='engine',
                             className='choice',
                             persistence=True)

datetime_from = DateTime.now() - timedelta(days=3 * 365)

date_choice = dcc.DatePickerSingle(id='date-from',
                                   date=datetime_from.date(),
                                   display_format=DATE_PICKER_FORMAT,
                                   className='choice',
                                   persistence=True)

score_choice = dcc.Input(id='score-choice',
                         type='number',
                         min=1, max=8, step=1, value=3,
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
        dcc.Store(id='xaxis-range'),
        dcc.Store(id='selected-security'),
        dbc.Col([
            dbc.Row([dbc.Col(env_choice), dbc.Col(interval_choice)], className='frame'),
            dbc.Row([dbc.Col(exchange_choice), dbc.Col(engine_choice)], className='frame'),
            dbc.Row([dbc.Col(date_choice), dbc.Col(score_choice)], className='frame'),
            dbc.Row(dbc.Col(security_table), className='scroll', style={'max-height': '35%'}),
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
               Input('interval-choice', 'value'),
               Input('env-choice', 'value'),
               Input('security-table', 'filter_query')])
def cb_security_table(exchange_name, engine_name, interval_name, env_name, query):
    if exchange_name and engine_name and interval_name and env_name:
        LOG.debug(f'Loading symbols with query: "{query or "*"}"')
        with store.ExchangeSeries() as exchange_series:
            securities = exchange_series[exchange_name]

        results = []
        boolean = ['[-]', '[+]']
        health_name = tool.health_name(engine_name, interval_name)
        result_name = tool.result_name(engine_name, interval_name, env_name)
        for security in securities:
            health = security[health_name]
            result = security[result_name]
            profit_ratio = result.profit / result.total if result.total else 0.0
            results += [dict(symbol=security.symbol,
                             shortable=boolean[security.shortable],
                             health=boolean[health],
                             profit_ratio=round(100 * profit_ratio, FLOAT_PRECISION - 2),
                             description=security.description,
                             profit=round(result.profit, FLOAT_PRECISION),
                             total=round(result.total, FLOAT_PRECISION),
                             volume=round(result.volume, FLOAT_PRECISION))]
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
               Input('interval-choice', 'value'),
               Input('env-choice', 'value'),
               Input('score-choice', 'value'),
               Input('selected-security', 'data')],
              [State('xaxis-range', 'data')])
def cb_series_graph(d_from, engine_name, interval_name, env_name, score, selected_security, xaxis_range):
    if d_from and engine_name and interval_name and env_name and selected_security:
        interval = {'1h': tool.INTERVAL_1H, '1d': tool.INTERVAL_1D}[interval_name]  # TODO: support 1h
        symbol = selected_security['symbol']
        if score:
            description = f"{selected_security['description']} [{100 * swings.limit_ratio(score)}%]"
        else:
            description = selected_security['description']

        # engine series
        engine = ENGINES[engine_name]
        dt_from = DateTime.parse_date(d_from)
        with engine.SecuritySeries(interval, dt_from=dt_from) as security_series:
            time_series = security_series[symbol]

        if time_series:
            # customize static data
            fields = ('timestamp', 'vma-50', 'vma-100', 'vma-200', 'volume', env_name)
            ts, vma_50, vma_100, vma_200, volume, trade = tool.transpose(time_series, fields)
            dts = [datetime.utcfromtimestamp(t) for t in ts]

            # customize swing data
            score_series = swings.display(time_series, score)
            ts, score_values = tool.transpose(score_series, ('timestamp', 'value'))
            score_dts = [datetime.utcfromtimestamp(t) for t in ts]
            score_custom = [s.to_dict() for s in score_series]

            # customize trade data
            fields = ('long', 'short', 'profit')
            long, short, profit = tool.transpose(trade, fields)
            trade_custom = [t.to_dict() for t in trade]

            # create traces
            score_trace = go.Scatter(x=score_dts, y=score_values, customdata=score_custom, name='Score',
                                     mode='lines', line=dict(width=1.0), showlegend=False)
            vma_50_trace = go.Scattergl(x=dts, y=vma_50, name='VMA-50',
                                        mode='lines', line=dict(width=1.0), visible='legendonly')
            vma_100_trace = go.Scattergl(x=dts, y=vma_100, name='VMA-100',
                                         mode='lines', line=dict(width=1.0))
            vma_200_trace = go.Scattergl(x=dts, y=vma_200, name='VMA-200',
                                         mode='lines', line=dict(width=1.0), visible='legendonly')
            long_trace = go.Scattergl(x=dts, y=long, customdata=trade_custom, name='Long',
                                      mode='markers', visible='legendonly')
            short_trace = go.Scattergl(x=dts, y=short, customdata=trade_custom, name='Short',
                                       mode='markers', visible='legendonly')
            profit_trace = go.Scattergl(x=dts, y=profit, customdata=trade_custom, name='Profit',
                                        mode='lines+markers', connectgaps=True, line=dict(width=1.0), showlegend=False)
            volume_trace = go.Bar(x=dts, y=volume, name='Volume', showlegend=False)

            # create a graph
            figure = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                                   row_heights=[0.6, 0.2, 0.2])
            figure.add_trace(score_trace, row=1, col=1)
            figure.add_trace(vma_50_trace, row=1, col=1)
            figure.add_trace(vma_100_trace, row=1, col=1)
            figure.add_trace(vma_200_trace, row=1, col=1)
            figure.add_trace(long_trace, row=1, col=1)
            figure.add_trace(short_trace, row=1, col=1)
            figure.add_trace(profit_trace, row=2, col=1)
            figure.add_trace(volume_trace, row=3, col=1)
            figure.update_xaxes(tickformat=XAXIS_FORMAT)
            figure.update_layout(margin=GRAPH_MARGIN, legend=LEGEND, title_text=description, hovermode='closest',
                                 xaxis=SPIKE, yaxis=SPIKE, plot_bgcolor=PLOT_BGCOLOR)
            figure.update_xaxes(range=xaxis_range or [dts[0], dts[-1]])
            return figure

    return go.Figure(data=[], layout=dict(margin=GRAPH_MARGIN, plot_bgcolor=PLOT_BGCOLOR))


@app.callback(Output('details-table', 'data'),
              [Input('selected-security', 'data')])
def cb_details_table(selected_security):
    results = [{'key': k, 'value': v} for k, v in selected_security.items()]
    return sorted(results, key=lambda d: d['key'])


@app.callback(Output('action-table', 'data'),
              [Input('series-graph', 'clickData')])
def cb_action_table(click_data):
    def convert_custom_data(date: str, datum: Dict) -> List[Dict]:
        result = []
        for k, v in datum.items():
            if k in ('_id', '_key', '_rev', 'timestamp'):
                pass
            elif k == 'open_timestamp':
                result += [{'date': date, 'key': 'open-date', 'value': DateTime.from_timestamp(v).format()}]
            elif k == 'open_long':
                result += [{'date': date, 'key': 'open-long', 'value': round(v, FLOAT_PRECISION)}]
            elif isinstance(v, float):
                result += [{'date': date, 'key': k, 'value': round(v, FLOAT_PRECISION)}]
            elif isinstance(v, dict):
                result += convert_custom_data(date, v)
            else:
                result += [{'date': date, 'key': k, 'value': v}]
        return result

    results = []
    if click_data:
        for p in click_data.get('points', []):
            cd = p.get('customdata')
            if cd:
                results += convert_custom_data(p['x'], cd)
    return sorted(results, key=lambda d: (d['date'], d['key']))


@app.callback(Output('xaxis-range', 'data'),
              [Input('series-graph', 'relayoutData')],
              [State('xaxis-range', 'data')])
def cb_relayout_data(relayout_data, xaxis_range):
    if relayout_data:
        if 'xaxis.autorange' in relayout_data:
            return None
        if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            return [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]
    return xaxis_range


def run_module(debug: bool):
    return app.run_server(debug=debug)


def main():
    debug = True
    log.init(__file__, debug=debug, to_screen=True)
    run_module(debug=debug)


if __name__ == '__main__':
    main()
