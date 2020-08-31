import re
from typing import Dict, List

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go
from dash.dependencies import Output, Input
from plotly.subplots import make_subplots

from src import store, tools, style

app = dash.Dash(external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.title = 'trend'

SYMBOL_COLUMNS = {'symbolId': 'Symbol', 'symbolType': 'Type', 'currency': 'Currency'}

symbol_table = dash_table.DataTable(
    id='symbol-table',
    columns=[{'name': v, 'id': k} for k, v in SYMBOL_COLUMNS.items()],
    filter_action='custom',
    row_selectable='single',
    **style.symbol_table(['symbolId', 'symbolType'])
)

data_graph = dcc.Graph(id='data-graph', className='graph')

dashboard = html.Div(
    [
        html.Div(symbol_table, className='three columns panel'),
        html.Div(data_graph, className='nine columns panel')
    ],
    className='dashboard row'
)

app.layout = dashboard

PATTERN = re.compile('{(\\w+)} contains (.+)')


def filter_instruments(instruments: List[Dict], filter_query) -> List[Dict]:
    # example: {symbolType} contains b && {symbolId} contains a && {currency} contains c
    if filter_query:
        matches = [re.search(PATTERN, f) for f in filter_query.split(' && ')]
        if all(matches):
            # noinspection PyTypeChecker
            columns = dict([m.groups() for m in matches])
            # filter-phrase in value for all filter-columns
            return [
                s for s in instruments
                if all(v.lower() in s[k].lower() for k, v in columns.items())
            ]
        else:
            return []
    else:
        return instruments


@app.callback(Output('symbol-table', 'data'),
              [Input('symbol-table', 'filter_query')])
def cb_symbol_table(filter_query):
    with store.FileStore('exchanges') as exchanges:
        instruments = sum([v for k, v in exchanges.items()], [])
        return [
            {c: s[c] for c in SYMBOL_COLUMNS}
            for s in filter_instruments(instruments, filter_query)
        ]


@app.callback(Output('data-graph', 'figure'),
              [Input('symbol-table', 'data'), Input('symbol-table', 'selected_rows')])
def cb_price_graph(data, selected_rows):
    if selected_rows:
        assert len(selected_rows) == 1
        row = data[selected_rows[0]]
        symbol = row['symbolId']
        with store.DBSeries(tools.DURATION_1D) as series:
            time_series = series[symbol]

        params = tools.transpose(time_series, ('timestamp', 'close', 'volume'))
        dates = [tools.from_ts_ms(ts, tz=tools.UTC_TZ) for ts in params['timestamp']]

        prices = go.Scatter(x=dates, y=params['close'], name='Price')
        volume = go.Bar(x=dates, y=params['volume'], name='Volume')
        figure = make_subplots(rows=2, cols=1,
                               shared_xaxes=True,
                               vertical_spacing=0.03,
                               row_heights=[0.7, 0.3],
                               specs=[[{'type': 'scatter'}], [{'type': 'bar'}]])
        figure.add_trace(prices, row=1, col=1)
        figure.add_trace(volume, row=2, col=1)
        figure.update_layout(showlegend=False, title_text=symbol)
        return figure

    return go.Figure(data=[])


if __name__ == '__main__':
    app.run_server(debug=True)
