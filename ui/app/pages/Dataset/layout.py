from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc
from dash import dash_table

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

# defintion of components for layout
# table_clients = dash_table.DataTable(
#     id='table-clients',
#     row_selectable='single',
#     filter_action='native',
#     page_action="native",
#     page_current= 0,
#     page_size= 10,
# )

## layout body
layout = html.Div([
    dbc.Row([dcc.Markdown(
    '''
    #### Data Understanding
    '''
    )]),
    # Dropdown Menu for DC and Pickup Date
    dbc.Row([
        dbc.Col([
            dcc.Loading(dcc.Graph(id = 'plot-clients-dc', style={"width": "100%", "height": "600px"}))
            #html.H5(id = "output-ghg")
            ],width = 6, align = 'center'),
        dbc.Col([
            dcc.Loading(dcc.Graph(id = 'plot-clients-per-dc', style={"width": "100%", "height": "600px"}))
            #html.H5(id = "output-ghg")
            ],width = 6, align = 'center')
    ], align="start", style = ROW_STYLE),
])