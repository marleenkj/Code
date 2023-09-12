import base64

from dash.dependencies import Input, Output
from dash import dcc, html
import dash_bootstrap_components as dbc

from app import app

from pages import page_list
from pages import home
from app import app_name

CONTENT_STYLE = {
    "margin-left": "4rem",
    "margin-right": "4rem",
    "padding": "2rem 1rem",
}

TOPBAR_STYLE = {
    "padding": "1rem 1rem",
    "font-size": 16,
    "font-weight": "bold",
}

NAVLINK_STYLE = {
    "margin-left": "2rem",
    "color": "#F0182D",
    #"font-size": 18,
    #"font-weight": 900,
}

encoded_logo = base64.b64encode(open('assets/Logo_TU.png', 'rb').read())
logo = html.Img(src='data:image/jpg;base64,{}'.format(encoded_logo.decode()), height='30px')
branding = dbc.Row(
    [dbc.Col(e) for e in [logo, dbc.NavbarBrand(app_name, className="ms-2")]],
    align="center",
    className="g-0",
)

pages = [dbc.NavLink(page.name, href=page.path, id=page.id_, style=NAVLINK_STYLE) for page in page_list]
navbar = dbc.Navbar(
    [html.A(branding, href=home.path, id=home.id_, style={"textDecoration": "none"}), ] + pages,
    color="dark",
    dark=True,
    style=TOPBAR_STYLE,
    class_name='ml-auto'
)

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    for page in page_list:
        if pathname == page.path:
            return page.layout
    return home.layout

app.layout = html.Div(
    [dcc.Location(id="url"), navbar, html.Div(id="page-content", style=CONTENT_STYLE)],
)

if __name__ == "__main__":
    app.run_server(port=5000, debug=True)

