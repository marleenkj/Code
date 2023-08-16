from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc
from dash import dash_table
from datetime import date

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

# defintion of components for layout
co2_emissions = dbc.Card([
    dbc.CardHeader('GHG Emissions road'),
    dbc.CardBody([html.H4(id = 'output-emissions-road-eval')])
], body=True, color = 'light')

co2_emissions_new = dbc.Card([
    dbc.CardHeader('GHG Emissions railroad'),
    dbc.CardBody([html.H4(id = 'output-emissions-railroad-eval')])
],body=True, color = 'light')

## layout body
layout = html.Div([
    dbc.Row([dcc.Markdown(
    '''
    #### Unimodal Road vs. Combined Railroad Freight Transportation
    '''
    )]),
    # Dropdown Menu for DC and Pickup Date
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    co2_emissions,
                    dcc.Loading(dcc.Graph(id = 'plot-co2-modell-road-eval')),
                ], width=6, align = 'center'),
                dbc.Col([
                    co2_emissions_new,
                    dcc.Loading(dcc.Graph(id = 'plot-co2-modell-railroad-eval')),
                ], width=6, align = 'center'),
            ], align="center", style = ROW_STYLE),
    ], align="start", style = ROW_STYLE)
    ])
])