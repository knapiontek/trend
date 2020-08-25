from datetime import datetime

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Output, Input

from src import store, config, tools

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')

SYMBOL_COLUMNS = ["symbolId", "symbolType", "currency"]

symbols_table = dash_table.DataTable(
    id='symbol-table',
    columns=[{'name': i.title(), 'id': i} for i in SYMBOL_COLUMNS],
    data=[],
    filter_action='native',
    row_selectable='single'
)

open_data = [33.0, 33.3, 33.5, 33.0, 34.1]
high_data = [33.1, 33.3, 33.6, 33.2, 34.8]
low_data = [32.7, 32.7, 32.8, 32.6, 32.8]
close_data = [33.0, 32.9, 33.3, 33.1, 33.1]
dates = [datetime(year=2013, month=10, day=10),
         datetime(year=2013, month=11, day=10),
         datetime(year=2013, month=12, day=10),
         datetime(year=2014, month=1, day=10),
         datetime(year=2014, month=2, day=10)]

scatter = go.Scatter(x=dates, y=open_data)
candles = go.Candlestick(x=dates,
                         open=open_data, high=high_data, low=low_data, close=close_data)
fig = go.Figure(data=[candles, scatter])
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
        open = [s['open'] for s in time_series]
        high = [s['high'] for s in time_series]
        low = [s['low'] for s in time_series]
        close = [s['close'] for s in time_series]
        _candles = go.Candlestick(x=_dates, open=open, high=high, low=low, close=close)
        return go.Figure(data=[_candles])

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
