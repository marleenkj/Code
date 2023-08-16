from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc
from dash import dash_table

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

# defintion of components for layout
table_ghg = dash_table.DataTable(
    id='table-ghg',
    row_selectable='single',
    filter_action='native',
    page_action="native",
    page_current= 0,
    page_size= 10,

)

## layout body
layout = html.Div([
    dbc.Row([dcc.Markdown(
    '''
    #### Analysis of different railroad transport systems: Combined, Intermodal, Multimodal
    '''
    )]),
    # Dropdown Menu for DC and Pickup Date
    dbc.Row([
        dbc.Col([
            #dcc.Loading(dcc.Graph(id = 'plot-map-route', style={"width": "100%", "height": "600px"}))
            #html.H5(id = "output-ghg")
            ],width = 6, align = 'center'),
        #dbc.Col(width = 1),
        dbc.Col([
            dbc.Stack([
                html.H5('Table with shipments grouped by client location'), 
                dcc.Loading(children=table_ghg)
            ], gap = 1),
        ], width={"size": 5, "offset": 1}, align = 'center')
    ], align="start", style = ROW_STYLE),
])