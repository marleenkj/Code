from dash import dcc, html
import dash_bootstrap_components as dbc

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

# layout body
layout = html.Div([
    dcc.Store(id="store"),
    dbc.Row([dcc.Markdown(
        '''
    #### Overview
    '''
    )]),
    # Dropdown Menu for DC and Pickup Date
    dbc.Row([
        dbc.Tabs(
            [
                dbc.Tab(label="Locations", tab_id="location"),
                dbc.Tab(label="Terminals", tab_id="terminal"),
                dbc.Tab(label="Results", tab_id="result"),
                dbc.Tab(label="Details", tab_id="detail"),
            ],
            id="tabs",
            active_tab="location",
        ),
        html.Div(id="tab-content", className="p-4"),
    ], align="start", style=ROW_STYLE),
])
