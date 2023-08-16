from dash.dependencies import Input, Output, State
from app import app, df_ghg, dict_points, dict_terminals, df_ghg_converted
from dash.exceptions import PreventUpdate
from loguru import logger
import io
import pandas as pd
import calendar
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

from ast import literal_eval
import sys
sys.path.append('../..')
from src.plots import graph_solution

@app.callback(
    Output('table-ghg', 'columns'),
    Input('url', 'pathname'),
)
def table_ghg_columns(_):
    format_int = {'locale': {}, 'nully': '',
                      'prefix': None, 'specifier': ',.0f'}
    format_float = {'locale': {}, 'nully': '',
                      'prefix': None, 'specifier': ',.2f'}
    format_date = {'locale': {}, 'nully': '',
    'prefix': None, 'specifier': ',.2f'}
    
    columns = [
        dict(id='date from', name='Date from'),
        dict(id='date to', name='Date to'),
        dict(id='co2 road', name='GHG road [kg]', type='numeric', format=format_float),
        dict(id='distance road', name='Distance road [m]', type='numeric', format=format_int),
        dict(id='co2 railroad', name='GHG railroad [kg]', type='numeric', format=format_float),
        dict(id='distance railroad', name='Distance railroad [m]', type='numeric', format=format_int)]
    return columns

@app.callback(
    Output('table-ghg', "data"),
    Input('url', 'pathname'),
)
def table_ghg(_):
    dff = df_ghg
    dff["date to"] = pd.DatetimeIndex(dff["date to"]).strftime("%Y-%m-%d")
    dff["date from"] = pd.DatetimeIndex(dff["date from"]).strftime("%Y-%m-%d")
    return dff.to_dict('records')

@app.callback(
    Output('plot-map-route', "figure"),
    Input('table-ghg', "derived_virtual_selected_rows"),
)
def plot_map(selected_rows_indices):
    dff = df_ghg_converted
    dict_term = dict_terminals
    fig = {}
    if (selected_rows_indices is None) or (selected_rows_indices == []):
        dict_routes = dff["routes railroad"].iloc[0]
        #fig = plot_railroad(dff, dict_routes, dict_term, "T4")
    else:
        print(selected_rows_indices[0])
        dict_routes = dff["routes railroad"].iloc[selected_rows_indices[0]]
        #fig = plot_railroad(dff, dict_routes, dict_term, "T4")
    return fig

