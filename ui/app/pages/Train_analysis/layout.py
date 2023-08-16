from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc
from dash import dash_table

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

## layout body
layout = html.Div([
    dbc.Row([dcc.Markdown(
    '''
    #### Impact Analysis for 2022
    '''
    )]),
    dbc.Row([
        dash_table.DataTable(id='table', row_selectable='single', page_size=10)
    ], align="start", style = ROW_STYLE),
    # Dropdown Menu for DC and Pickup Date
    dbc.Row([
        dcc.Graph(id = 'plot-map-train', style={"width": "100%", "height": "600px"})
    ], align="start", style = ROW_STYLE)

])