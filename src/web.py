import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go
from dash.dependencies import Output, Input

from src import store, config, tools, style

app = dash.Dash(external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

SYMBOL_COLUMNS = ["symbolId", "symbolType", "currency"]

symbol_table = dash_table.DataTable(
    id='symbol-table',
    columns=[{'name': i.title(), 'id': i} for i in SYMBOL_COLUMNS],
    filter_action='native',
    row_selectable='single',
    **style.symbol_table(['symbolId', 'symbolType'])
)

data_graph = dcc.Graph(id='data-graph', style=style.data_graph)

dashboard = html.Div(
    [
        dcc.Store(id='nil-store', storage_type='local'),
        html.Div([
            html.Div(symbol_table, className="three columns", style=style.panel),
            html.Div(data_graph, className="nine columns", style=style.panel)
        ], className='row'),
    ],
    style=style.dashboard
)

app.layout = dashboard


@app.callback(Output('symbol-table', 'data'),
              [Input('nil-store', 'data')])
def cb_symbol_table(data):
    with store.FileStore('exchanges') as exchanges:
        symbols = sum([v for k, v in exchanges.items()], [])
        return [{c: s[c] for c in SYMBOL_COLUMNS} for s in symbols]


@app.callback(Output('data-graph', 'figure'),
              [Input('symbol-table', 'data'), Input('symbol-table', 'selected_rows')])
def cb_price_graph(data, selected_rows):
    if selected_rows:
        assert len(selected_rows) == 1
        row = data[selected_rows[0]]
        symbol = row['symbolId']
        with store.DBSeries(config.DURATION_1D) as series:
            time_series = series['MCFT.NASDAQ']

        dates = [tools.from_ts_ms(s['timestamp'], tz=config.UTC_TZ) for s in time_series]
        params = tools.transpose(time_series, ['close'])
        candles = go.Scatter(x=dates, y=params['close'])
        figure = go.Figure(data=[candles], layout={'title': 'XOM.NYSE'})
        return figure

    return go.Figure(data=[])


if __name__ == '__main__':
    app.run_server(debug=True)
