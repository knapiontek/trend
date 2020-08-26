from collections import defaultdict
from typing import List, Dict

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go
from dash.dependencies import Output, Input

from src import store, config, tools

app = dash.Dash(external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

SYMBOL_COLUMNS = ["symbolId", "symbolType", "currency"]

style_cell_conditional = [
    {
        'if': {'column_id': c},
        'text-align': 'left'
    } for c in ['symbolId', 'symbolType']
]
style_data_conditional = [
    {
        'if': {'row_index': 'odd'},
        'background-color': 'rgb(229, 236, 246)'
    }
]
style_header = {
    'background-color': 'rgb(200, 212, 227)',
    'font-weight': 'bold'
}

symbol_table = dash_table.DataTable(
    id='symbol-table',
    columns=[{'name': i.title(), 'id': i} for i in SYMBOL_COLUMNS],
    filter_action='native',
    row_selectable='single',
    style_cell_conditional=style_cell_conditional,
    style_data_conditional=style_data_conditional,
    style_header=style_header
)

price_graph = dcc.Graph(id='price-graph')

dashboard_style = {'height': '900px',
                   'border-style': 'solid',
                   'border-width': 'thin',
                   'overflow-x': 'hidden',
                   'overflow-y': 'auto'}

dashboard = html.Div(
    [
        dcc.Store(id='trend-store', storage_type='local'),
        html.Div([
            html.Div(symbol_table, className="three columns", style=dashboard_style),
            html.Div(price_graph, className="nine columns", style=dashboard_style)
        ], className='row'),
    ],
    style={'margin': '20px'}
)

app.layout = dashboard


@app.callback(Output('symbol-table', 'data'),
              [Input('trend-store', 'data')])
def cb_symbol_table(data):
    with store.FileStore('exchanges') as exchanges:
        symbols = sum([v for k, v in exchanges.items()], [])
        return [{c: s[c] for c in SYMBOL_COLUMNS} for s in symbols][:100]


def transpose(lst: List[Dict], keys: List[str]) -> Dict[str, List]:
    dt = defaultdict(list)
    for i in lst:
        for k in keys:
            dt[k].append(i[k])
    return dt


@app.callback(Output('price-graph', 'figure'),
              [Input('symbol-table', 'data'), Input('symbol-table', 'selected_rows')])
def cb_price_graph(data, selected_rows):
    if selected_rows:
        assert len(selected_rows) == 1
        row = data[selected_rows[0]]
        symbol = row['symbolId']
        with store.DBSeries(config.DURATION_1D) as series:
            time_series = series['XOM.NYSE']

        _dates = [tools.from_ts_ms(s['timestamp'], tz=config.UTC_TZ) for s in time_series]
        params = transpose(time_series, ['open', 'high', 'low', 'close'])
        candles = go.Scatter(x=_dates, y=params['close'])
        figure = go.Figure(data=[candles])
        # figure.update_xaxes(range=['2020-03-01', '2020-03-15'])
        return figure

    return go.Figure(data=[])


if __name__ == '__main__':
    app.run_server(debug=True)
