import dash
import dash_bootstrap_components as dbc
import dash_html_components as html

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

row = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(dbc.Card("One of three columns", className="m-5"), md=4),
                dbc.Col(dbc.Card("One of three columns", className="m-5"), md=4),
                dbc.Col(dbc.Card("One of three columns", className="m-5"), md=4),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Div("One of four columns"), width=6, lg=3),
                dbc.Col(html.Div("One of four columns"), width=6, lg=3),
                dbc.Col(html.Div("One of four columns"), width=6, lg=3),
                dbc.Col(html.Div("One of four columns"), width=6, lg=3),
            ]
        ),
    ]
)

app.layout = html.Div([
    dbc.Alert("Hello, Bootstrap!", className="m-5"),
    row
])

if __name__ == "__main__":
    app.run_server(debug=True)
