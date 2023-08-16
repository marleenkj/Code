import os
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

cards = html.Div([
    dbc.Row([
    ]),
    dbc.Row([
    ])
])

layout = dbc.Container([dcc.Markdown(
    f''' 
    ## Sustainable Assessment of Combined Railroad Freight Transportation
    
    1. Individual Client Analysis
    2. Combined Railroad Freight Analysis
    3. Transport System Analysis
    4. Sensitivity Analysis
    ''')
])
