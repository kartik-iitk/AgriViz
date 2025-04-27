import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# import page layouts + callback‐registrars
from pages.home import layout as home_layout
from pages.kcc import layout as kcc_layout, register_callbacks as register_kcc
from pages.price import layout as price_layout, register_callbacks as register_price

# 1) init app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# 2) assemble multipage layout
app.layout = dbc.Container(
    [
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("Home", href="/", id="link-home")),
                dbc.NavItem(dbc.NavLink("KCC", href="/kcc", id="link-kcc")),
                dbc.NavItem(dbc.NavLink("Price", href="/price", id="link-price")),
            ],
            brand="CS661 Project",
            color="dark",
            dark=True,
        ),
        html.Br(),
        dcc.Location(id="url", refresh=False),
        html.Div(
            id="page-content",
            children=[
                html.Div(home_layout, id="page-home", style={"display": "block"}),
                html.Div(kcc_layout, id="page-kcc", style={"display": "none"}),
                html.Div(price_layout, id="page-price", style={"display": "none"}),
            ],
        ),
    ],
    fluid=True,
)


# 3) page‐switch callback
@app.callback(
    Output("page-home", "style"),
    Output("page-kcc", "style"),
    Output("page-price", "style"),
    Input("url", "pathname"),
)
def display_page(pathname):
    if pathname == "/":
        return {"display": "block"}, {"display": "none"}, {"display": "none"}
    elif pathname == "/kcc":
        return {"display": "none"}, {"display": "block"}, {"display": "none"}
    elif pathname == "/price":
        return {"display": "none"}, {"display": "none"}, {"display": "block"}
    else:
        # fallback: hide all
        return {"display": "none"}, {"display": "none"}, {"display": "none"}


# 4) register each page's callbacks
register_kcc(app)
register_price(app)

if __name__ == "__main__":
    app.run(debug=True)
