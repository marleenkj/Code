from dash.dependencies import Input, Output, State
from app import app, df_limited, dict_terminals
from dash.exceptions import PreventUpdate
from dash import dcc, dash_table, html
import dash_bootstrap_components as dbc
from dash import dash_table
from loguru import logger
import io
import pandas as pd
import datetime as dt
import calendar
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import date
import time

import sys
sys.path.append('../..')
from src.plots import show_clients_per_dc, show_clients_dc, show_clients_per_dc_and_both

from plotly.subplots import make_subplots
import plotly.graph_objects as go

def waterfall_plot(dict_list_values):
    dict_values = {}
    for i in dict_list_values.keys():
        list_values = list(range(4))
        list_values[0] = dict_list_values[i][0]
        list_values[2] = dict_list_values[i][1]
        list_values[1] = list_values[2] - list_values[0]
        list_values[3] = (list_values[2]/list_values[0])-1
        dict_values[i] = list_values
        
    fig = make_subplots(rows=1, cols=3, 
                        shared_yaxes=True)
    list_horizons = list(dict_list_values.keys())
    for j in range(len(list_horizons)):
        list_measures = dict_values[list_horizons[j]]
        fig.add_trace(go.Waterfall(
            name = list_horizons[j], orientation = "v",
            measure = [ "absolute", "relative", "absolute"],
            x = ["GHG Road", "Include Rail", "GHG Railroad"],
            textposition = "outside",
            text = [f"{list_measures[0]:,.0f}", 
                    u"Δ "+f"{list_measures[1]:+,.0f} t<br>"+u"Δ "+f"{list_measures[3]:+.1%}", 
                    f"{list_measures[2]:,.0f}"],
            y = list_measures,
            decreasing = {"marker":{"color":"rgb(87, 179, 142)"}},
            increasing = {"marker":{"color":"darkred"}},
            totals = {"marker":{"color":"lightgrey"}},
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ), row = 1, col = j+1)
    fig.update_xaxes(title = "daily", row = 1, col = 1)
    fig.update_xaxes(title = "bi-daily", row = 1, col = 2)
    fig.update_xaxes(title = "weekly", row = 1, col = 3)
    fig.update_yaxes(range = [0,max(max(list(dict_list_values.values())))+1000])
    fig.update_yaxes(title = "Total GHG emissions [t Co2-eq]", row = 1, col = 1)
    fig.update_layout(showlegend = False, waterfallgap = 0.2)
    return fig

def waterfall_plot_volumes(dict_list_volumes):
    fig = make_subplots(rows=3, cols=3, 
                        shared_yaxes=True,
                       shared_xaxes=True,
                       subplot_titles=('Daily',  'Bi-Daily', 'Weekly'),
                        y_title = "GHG Emissions [tCO2-eq.]",
                       horizontal_spacing = 0.05,
                       vertical_spacing = 0.05)
    for i in range(len(dict_list_volumes.keys())):
        volume = list(dict_list_volumes.keys())[i]
        dict_list_values = dict_list_volumes[volume]
        max_value = []
        for j in range(len(dict_list_values.keys())):
            horizon = list(dict_list_values.keys())[j]
            print(dict_list_values)
            list_values = list(range(4))
            list_values[0] = dict_list_values[horizon][0]
            list_values[2] = dict_list_values[horizon][1]
            list_values[1] = list_values[2] - list_values[0]
            list_values[3] = (list_values[2]/list_values[0])-1
            fig.add_trace(go.Waterfall(
                name = horizon, orientation = "v",
                measure = [ "absolute", "relative", "absolute"],
                x = ["GHG Road", "Include Rail", "GHG Railroad"],
                textposition = "outside",
                text = [f"", 
                           u"Δ "+f"{list_values[3]:+.1%}", 
                        f""],
                y = list_values,
                decreasing = {"marker":{"color":"rgb(87, 179, 142)"}},
                increasing = {"marker":{"color":"darkred"}},
                totals = {"marker":{"color":"lightgrey"}},
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ), row = i+1, col = j+1)
            max_value.append(max(list_values))
            fig.update_yaxes(range = [0,5000], nticks = 3, row = i+1, col = j+1)
        #fig.update_yaxes(range = [0,max(max_value)*1.4], row = i+1, col = 1)
        fig.update_yaxes(range = [0,5000], nticks = 3, row = i+1, col = 1)
        fig.update_yaxes(side = "right", col = 3)
    fig.update_layout(showlegend = False, waterfallgap = 0.2, height = 600, yaxis2 = {"overlaying":"y","side": "right"})
    return fig

def show_terminals(dict_terminals):
    fig = go.Figure()
    for i in dict_terminals.keys():
        fig.add_trace(go.Scattermapbox(lat=[dict_terminals[i][0]], lon=[dict_terminals[i][1]], 
                                   mode = 'markers', marker = {'size': 12}, name = f"{i}"))
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 40}, mapbox={
                      'zoom': 4, "center": {'lat': 45, 'lon': 3}})
    fig.update_layout(height = 500, width = 700, colorway = px.colors.qualitative.Pastel)
    return fig

@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "active_tab"), Input("store", "data")],
)
def render_tab_content(active_tab, data):
    """
    This callback takes the 'active_tab' property as input, as well as the
    stored graphs, and renders the tab content depending on what the value of
    'active_tab' is.
    """
    if active_tab and data is not None:
        if active_tab == "result":
            return dcc.Graph(figure=data["waterfall_volumes"])
        elif active_tab == "location":
            return dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=data["location_1"]), width=6),
                    dbc.Col(dcc.Graph(figure=data["location_2"]), width=6),
                ]
            )
        elif active_tab == "detail":
            return dbc.Row(
                [
                    dbc.Col([
                        dbc.Row(dcc.Graph(figure=data["waterfall_1"])),
                        dbc.Row(dcc.Graph(figure=data["waterfall_5"])),
                        dbc.Row(dcc.Graph(figure=data["waterfall_10"]))
                        ])
                ]
            )
        elif active_tab == "terminal":
            return dcc.Graph(figure=data["terminals"])
    return "No tab selected"

@app.callback(
    Output("store", "data"), 
    Input('url', 'pathname'),
)
def generate_graphs(_):
    """
    This callback generates three simple graphs from random data.
    """
    # simulate expensive graph generation process
    time.sleep(2)

    start_date = "2022-01-03"
    end_date = "2022-01-05"
    df = df_limited
    df = df[(df["Delivery date"]>start_date)&(df["Delivery date"]<end_date)]
    fig_clients_per_dc = show_clients_per_dc_and_both(df)

    start_date = "2022-01-03"
    end_date = "2022-01-05"
    df = df_limited
    df = df[(df["Delivery date"]>start_date)&(df["Delivery date"]<end_date)]
    fig_clients = show_clients_dc(df)

    dict_volumes = {1: {'daily': [2474.211048355151, 2855.909850260001],
                        'bi-daily': [1798.9428593004848, 1977.9757442228467],
                        'weekly': [822.6323108917265, 804.3028958804282]},
                    5: {'daily': [2998.0916124438204, 3031.6963341580367],
                        'bi-daily': [2384.8728471962845, 2156.2915170426418],
                        'weekly': [1492.5743710181257, 984.0532368430867]},
                    10: {'daily': [3636.115416588048, 3208.1489243943365],
                        'bi-daily': [2906.4652262506374, 2351.5807199582528],
                        'weekly': [2449.4755938491344, 1314.8931931946083]}}

    fig_waterfall_volumes = waterfall_plot_volumes(dict_volumes)
    fig_waterfall_1 = waterfall_plot(dict_volumes[1])
    fig_waterfall_5 = waterfall_plot(dict_volumes[5])
    fig_waterfall_10 = waterfall_plot(dict_volumes[10])

    fig_terminals = show_terminals(dict_terminals)

    # save figures in a dictionary for sending to the dcc.Store
    return {
        "location_1": fig_clients, 
        "location_2": fig_clients_per_dc, 
        "waterfall_volumes": fig_waterfall_volumes,
        "waterfall_1": fig_waterfall_1,
        "waterfall_5": fig_waterfall_5,
        "waterfall_10": fig_waterfall_10,
        "terminals": fig_terminals,
        }
