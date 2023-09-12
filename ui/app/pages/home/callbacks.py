from src.plots import show_clients_per_dc, show_clients_dc
from dash.dependencies import Input, Output
from app import app, df_limited
import sys
sys.path.append('../..')


@app.callback(
    Output('plot-clients-dc', 'figure'),
    Input('url', 'pathname'),
)
def plot_clients(_):
    start_date = "2022-01-03"
    end_date = "2022-01-05"
    df = df_limited
    df = df[(df["Delivery date"] > start_date)
            & (df["Delivery date"] < end_date)]
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
    df = df[(df["Delivery date"] > start_date)
            & (df["Delivery date"] < end_date)]
    fig_clients_per_dc = show_clients_per_dc(df)
    return fig_clients_per_dc
