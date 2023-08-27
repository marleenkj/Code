from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc
from dash import dash_table
from datetime import date

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

# defintion of components for layout
date_picker_range = dcc.DatePickerRange(
                id='date-picker-range',
                min_date_allowed=date(2022, 1, 1),
                max_date_allowed=date(2022, 12, 31),
                initial_visible_month=date(2022, 1, 3),
                start_date=date(2022, 1, 3),
                end_date=date(2022, 1, 4)
            )

filter_card = dbc.Card([
    # DC filter
    dbc.Stack([
        html.H4('Filters'),
        # Month filter
        html.Div([
            dbc.Label("Select a planning period: "),
            date_picker_range
        ]),
        #html.Div(id='output-container-date-picker-range'),
        # DC filter
        html.Div([
            dbc.Label("Select a distribution center: "),
            dcc.Dropdown(id="dropdown-shipper", style = FONT_STYLE),
            html.Div(id='output-closest-dct'),
        ]),
        # Terminal filter
        html.Div([
            dbc.Label("Select terminals: "),
            dcc.Dropdown(id="dropdown-terminal", multi = True, style = FONT_STYLE)
        ]),
        # Clients filter
        html.Div([
            dbc.Label("Select clients: "),
            dcc.Dropdown(id="dropdown-clients", multi = True, style = FONT_STYLE)
        ])
    ], gap=3)
], body=True)

co2_emissions = dbc.Card([
    dbc.CardHeader('GHG Emissions road'),
    dbc.CardBody([html.H4(id = 'output-emissions-road')])
], body=True, color = 'light')

co2_emissions_new = dbc.Card([
    dbc.CardHeader('GHG Emissions railroad'),
    dbc.CardBody([html.H4(id = 'output-emissions-railroad')])
],body=True, color = 'light')

# collapse_button = dbc.Button(
#             "More details",
#             id="button-table-calculation",
#             className="mb-3",
#             color="primary",
#             n_clicks=0,
#         )

# collapse_df = dbc.Collapse(
#             dash_table.DataTable(id='table-calculation'),
#             id="collapse",
#             is_open=False,
#         )

table_co2_modell = dash_table.DataTable(id='table-co2-modell')

## layout body
layout = html.Div([
    dbc.Row([dcc.Markdown(
    '''
    #### Sustainable Assessment of Combined Railroad Freight Transportation
    '''
    )]),
    # Dropdown Menu for DC and Pickup Date
    dbc.Row([
        dbc.Col([
            filter_card,
            html.Button('Execute', id='button-execute'),
            ],width = 4, align = 'start'),
        #dbc.Col(width = 1),
        dbc.Col([
            #dcc.Markdown('#### Results'),
            dbc.Row([
                #dcc.Loading(dbc.Stack([
                dbc.Col([
                    co2_emissions,
                    dcc.Loading(dcc.Graph(id = 'plot-co2-modell-road')),
                ], width=6, align = 'center'),
                dbc.Col([
                    co2_emissions_new,
                    dcc.Loading(dcc.Graph(id = 'plot-co2-modell')),
                ], width=6, align = 'center'),
                #], direction = "horizontal")),
            ], align="center"),                   
            table_co2_modell
            ], width={"size": 8, "offset": 0}, align = 'center')
    ], align="start", style = ROW_STYLE),
])