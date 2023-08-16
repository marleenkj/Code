from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc
from dash import dash_table

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

# defintion of components for layout
table_clients = dash_table.DataTable(
    id='table-clients-truck',
    page_current= 0,
    page_size= 10,
)

ftl_truck = dbc.Card([
    dbc.CardBody([
        dcc.Markdown('#### Full truck load'),
        dcc.Loading(dcc.Graph(
            id = 'plot-pie-truck', 
            #style={"width": "100%", "height": "400px"}
            )),
        dcc.Loading(dcc.Graph(
            id = 'plot-boxplot-truck', 
            style={"width": "100%", "height": "300px"}
            ))
    ])
], body=True, color = 'light')

ftl_train = dbc.Card([
    dbc.CardBody([
        dcc.Markdown('#### Full train load'),
                dcc.Loading(dcc.Graph(
            id = 'plot-pie-train', 
            #style={"width": "100%", "height": "400px"}
            )),
        dcc.Loading(dcc.Graph(
            id = 'plot-boxplot-train', 
            style={"width": "100%", "height": "300px"}
            ))
    ])
], body=True, color = 'light')


## layout body
layout = html.Div([
    dbc.Row([dcc.Markdown(
    '''
    #### Individual client analysis for direct delivery
    '''
    )]),
    # Dropdown Menu for DC and Pickup Date
    dbc.Row([
        dbc.Col([
            ftl_truck
            ],width = 6, align = 'center'),
        dbc.Col([
            ftl_train
            ],width = 6, align = 'center'),
    ], align="center", style = ROW_STYLE),
    dbc.Row([
        dbc.Col([
            table_clients,
            dcc.Dropdown(id="dropdown-client", style = FONT_STYLE),
            ], width = 6, align = 'center'),
        dbc.Col([
            dcc.Loading(dcc.Graph(id = 'plot-routing', style={"width": "100%", "height": "300px"})),
        ],width = 6, align = 'center'),
    ], align="start", style = ROW_STYLE),
])