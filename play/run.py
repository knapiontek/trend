import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go

df = pd.read_csv('ogzd.uk.csv')

start = pd.Timestamp(2017, 3, 20)


def convert_date(no: int) -> pd.Timestamp:
    year = int(no // 1e4)
    month = int(no % 1e4 // 1e2)
    day = int(no % 1e2)
    return pd.Timestamp(year=year, month=month, day=day)


df['DATE1'] = df['DATE'].apply(convert_date)
df = df[df.DATE1 > start]

df['EMA'] = df.loc[:, 'CLOSE'].ewm(span=26, adjust=False).mean()

candles = go.Candlestick(x=df['DATE1'],
                         open=df['OPEN'],
                         high=df['HIGH'],
                         low=df['LOW'],
                         close=df['CLOSE'])

ema = go.Scatter(x=df['DATE1'], y=df['EMA'])

fig = go.Figure(data=[ema, candles])

app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig, style={'height': 1000})
])

app.run_server(debug=True, use_reloader=False)
