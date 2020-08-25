from collections import defaultdict
from typing import List, Dict

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go
from dash.dependencies import Output, Input

from src import store, config, tools

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

SYMBOL_COLUMNS = ["symbolId", "symbolType", "currency"]

symbols_table = dash_table.DataTable(
    id='symbol-table',
    columns=[{'name': i.title(), 'id': i} for i in SYMBOL_COLUMNS],
    data=[],
    filter_action='native',
    row_selectable='single'
)

fig = go.Figure(data=[])
price_graph = dcc.Graph(id='price-graph', figure=fig, style={'height': '100%'})

dashboard = html.Div(
    [
        dcc.Store(id='trend-store', storage_type='local'),
        dbc.Row([
            dbc.Col(symbols_table, md=2),
            dbc.Col(price_graph, md=10),
        ])
    ], style={'height': '100%', 'overflow-x': 'hidden', 'overflow-y': 'hidden'}
)

app.layout = dashboard


@app.callback(Output('symbol-table', 'data'),
              [Input('trend-store', 'data')])
def cb_symbol_table(data):
    with store.FileStore('exchanges') as exchanges:
        symbols = sum([v for k, v in exchanges.items()], [])
        return [{c: s[c] for c in SYMBOL_COLUMNS} for s in symbols][:30]


def transpose(lst: List[Dict], keys: List[str]) -> Dict[str, List]:
    dt = defaultdict(list)
    for i in lst:
        for k in keys:
            dt[k].append(i[k])
    return dt


@app.callback(Output('price-graph', 'figure'),
              [Input('symbol-table', 'data'), Input('symbol-table', 'selected_rows')])
def cb_symbol_table(data, selected_rows):
    if selected_rows:
        assert len(selected_rows) == 1
        row = data[selected_rows[0]]
        symbol = row['symbolId']
        with store.DBSeries(config.DURATION_1D) as series:
            time_series = series['XOM.NYSE'][-200:]

        _dates = [tools.from_ts_ms(s['timestamp'], tz=config.UTC_TZ) for s in time_series]
        params = transpose(time_series, ['open', 'high', 'low', 'close'])
        candles = go.Candlestick(x=_dates, **params)
        return go.Figure(data=[candles])

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
