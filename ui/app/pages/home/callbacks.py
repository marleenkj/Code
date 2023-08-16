from dash.dependencies import Input, Output, State
from app import app, df_limited
from dash.exceptions import PreventUpdate
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

import sys
sys.path.append('../..')
from src.plots import show_clients_per_dc, show_clients_dc

@app.callback(
    Output('plot-clients-dc', 'figure'),
    Input('url', 'pathname'),
)
def plot_clients(_):
    start_date = "2022-01-03"
    end_date = "2022-01-05"
    df = df_limited
    df = df[(df["Delivery date"]>start_date)&(df["Delivery date"]<end_date)]
    fig_clients = show_clients_dc(df)
    return fig_clients

@app.callback(
    Output('plot-clients-per-dc', 'figure'),
    Input('url', 'pathname'),
)
def plot_clients_per_dc(_):
    start_date = "2022-01-03"
    end_date = "2022-01-05"
    df = df_limited
    df = df[(df["Delivery date"]>start_date)&(df["Delivery date"]<end_date)]
    fig_clients_per_dc = show_clients_per_dc(df)
    return fig_clients_per_dc