from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc
from dash import dash_table

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

# defintion of components for layout
shipments_table = dash_table.DataTable(
    id='table-shipments-grouped',
    page_current=0,
    page_size=10,
    page_action='custom',
    filter_action='custom',
    filter_query='',
    sort_action='custom',
    sort_mode='single',
    sort_by=[],
    row_selectable='multi',
    style_cell_conditional=[
        {'if': {'column_id': c},
         'textAlign': 'left'
         } for c in ['Client name']
    ]
)

filter_card = dbc.Card([
    # DC filter
    dbc.Stack([
        html.H4('Filters'),
        html.Div([
            dbc.Label("Select a DC : "),
            dcc.Dropdown(id="dropdown-shipper", style=FONT_STYLE)
        ]),
        # Month filter
        html.Div([
            dbc.Label("Select a month: "),
            dcc.Dropdown(id="dropdown-month", style=FONT_STYLE)
        ]),
        # Max distance filter
        html.Div([
            dbc.Label("Maximum distance of electric vehicles:"),
            dbc.Input(id='input-distance-bev',
                      value=200, type='number',
                      style=FONT_STYLE)
        ])
    ], gap=3)
], body=True)

co2_emissions = dbc.Card([
    dbc.CardHeader('Total Carbon Emissions'),
    dbc.CardBody([html.H4(id='output-emissions')])
], body=True, color='light')

co2_emissions_new = dbc.Card([
    dbc.CardHeader('Total CO2 emissions savings with EV'),
    dbc.CardBody([html.H4(id='output-emissions-savings')])
], body=True, color='light')

co2_emissions_savings = dbc.Card([
    dbc.CardHeader('Relative CO2 emissions savings with EV'),
    dbc.CardBody([html.H4(id='output-emissions-savings-share')])
], body=True, color='light')

#instruction_graph = html.H5(id = 'title-plot-bar-shipments', style = COLOR_SE)

collapse_button = dbc.Button(
    "More details",
    id="button-table-shipments-client",
    className="mb-3",
    color="primary",
    n_clicks=0,
)

collapse_df = dbc.Collapse(
    dash_table.DataTable(id='table-shipments-client'),
    id="collapse",
    is_open=False,
)

# layout body
layout = html.Div([
    dbc.Row([dcc.Markdown(
        '''
    #### Impact Analysis for 2022
    '''
    )]),
    # Dropdown Menu for DC and Pickup Date
    dbc.Row([
        dbc.Col([
                filter_card
                ], width=3, align='center'),
        #dbc.Col(width = 1),
        dbc.Col([
            dbc.Stack([
                html.H5('Table with shipments grouped by client location'),
                dcc.Loading(children=shipments_table)
            ], gap=1),
            dcc.Download(id="download-csv"),
            dbc.Button("Save to csv file", id="button-save-csv")
        ], width={"size": 7, "offset": 1}, align='center')
    ], align="start", style=ROW_STYLE),
    html.Hr(),
    # Card and data
    dbc.Row([
        dbc.Stack([
            dbc.Col([
                dbc.Stack([
                    co2_emissions,
                    co2_emissions_new,
                    co2_emissions_savings
                ], gap=4)
            ], width=3, align='center'),
            dbc.Col([
                dcc.Loading(
                    children=dcc.Graph(
                        id='plot-map',
                        style={
                            "width": "100%",
                            "height": "600px"}))
            ], width=4, align='center'),
            dbc.Col([
                # instruction_graph,
                dcc.Loading(
                    children=dcc.Graph(
                        id='plot-bar-shipments',
                        style={
                            "width": "100%",
                            "height": "600px"})),
                collapse_button
            ], width=5, align='center')], gap=5, direction='horizontal')
    ], align="start", style=ROW_STYLE),
    dbc.Row([
        dbc.Col(width=3),
        dbc.Col(width=4),
        dbc.Col(collapse_df, width=5, align='center'),
    ], align="center", style=ROW_STYLE)
])
