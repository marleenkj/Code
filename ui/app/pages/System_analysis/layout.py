from dash import dcc, html
import dash_bootstrap_components as dbc

ROW_STYLE = {"padding": "1rem 1rem"}
FONT_STYLE = {"font-family": "inherit"}
COLOR_SE = {"color": "#36C746"}

# defintion of components for layout
co2_emissions_combined = dbc.Card([
    dbc.CardHeader('GHG Emissions combined'),
    dbc.CardBody([html.H4(id='output-emissions-combined')])
], body=True, color='light')

co2_emissions_intermodal = dbc.Card([
    dbc.CardHeader('GHG Emissions intermodal'),
    dbc.CardBody([html.H4(id='output-emissions-intermodal')])
], body=True, color='light')

co2_emissions_multimodal = dbc.Card([
    dbc.CardHeader('GHG Emissions multimodal'),
    dbc.CardBody([html.H4(id='output-emissions-multimodal')])
], body=True, color='light')

# layout body
layout = html.Div([
    dbc.Row([dcc.Markdown(
        '''
    #### Combined vs. Intermodal Freight Transportation
    '''
    )]),
    # Dropdown Menu for DC and Pickup Date
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    co2_emissions_combined,
                    dcc.Loading(dcc.Graph(id='plot-co2-modell-combined')),
                ], width=6, align='center'),
                dbc.Col([
                    co2_emissions_intermodal,
                    dcc.Loading(dcc.Graph(id='plot-co2-modell-intermodal',
                                          #style={"width": "100%", "height": "600px"}
                                          )),
                ], width=6, align='center'),
                # dbc.Col([
                #     co2_emissions_multimodal,
                #     dcc.Loading(dcc.Graph(id = 'plot-co2-modell-multimodal',
                #                     #style={"width": "100%", "height": "600px"}
                #                     )),
                # ], width=4, align = 'center'),
            ], align="center", style=ROW_STYLE),
            dbc.Row([
                dbc.Col([
                    html.Div(id="table-combined")
                ], width=6, align='start'),
                dbc.Col([
                    html.Div(id="table-intermodal")
                ], width=6, align='start'),
            ], align="center", style=ROW_STYLE),
        ], align="start", style=ROW_STYLE)
    ])
])
