from dash.dependencies import Input, Output, State
from app import app, df_train
from dash.exceptions import PreventUpdate
from loguru import logger
import io
import pandas as pd
import calendar
import numpy as np

# functions
import pandas as pd
import calendar
import plotly.graph_objects as go
import datetime as dt

def show_map_marker_lines(index):
    x = df_train.iloc[index]
    fig = go.Figure()
    columns_car = ['Receiver', 'Shipper']
    append_lat = ' latitude'
    append_long = ' longitude'
    columns_train = ['Shipper', 'DC-T terminal', 'T-C terminal', 'Receiver']
    fig.add_trace(go.Scattermapbox(lat=[x['Shipper latitude']], lon=[x['Shipper longitude']], mode = 'markers', marker = {'size': 10}, name = 'shipper'))
    fig.add_trace(go.Scattermapbox(lat=[x['Receiver latitude']], lon=[x['Receiver longitude']], mode = 'markers', marker = {'size': 10}, name = 'receiver'))
    fig.add_trace(go.Scattermapbox(lat=x[[sub + append_lat for sub in columns_car]], lon=x[[sub + append_long for sub in columns_car]], mode = 'markers+lines', name = 'car'))
    fig.add_trace(go.Scattermapbox(lat=x[[sub + append_lat for sub in columns_train]], lon=x[[sub + append_long for sub in columns_train]], mode = 'markers+lines', name = 'train'))
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 40}, mapbox={
                      'zoom': 5, "center": {'lat': df_train[[sub + append_lat for sub in columns_train]].iloc[index].mean(), 'lon': df_train[[sub + append_long for sub in columns_train]].iloc[index].mean()}})
    fig.update_layout(mapbox_style="open-street-map")
    return fig


@app.callback(
    Output('table', 'columns'),
    Input('url', 'pathname'),
)
def table_shipments_columns(_):    
    columns = [
        dict(id='DC name', name='DC name'),
        dict(id='Receiver address', name='Receiver address'),
        dict(id='Receiver city', name='Receiver city'),
        dict(id='Receiver country', name='Receiver country'),
        dict(id='Receiver address', name='Receiver address'),
        dict(id='DC-T name', name='DC-T name'),
        dict(id='T-C name', name='T-C name'),
        dict(id='Distance total', name='Distance total'),
        dict(id='Distance direct', name='Distance direct')]
    return columns

@app.callback(
    Output('table', "data"),
    Input('url', 'pathname')
)
def show_datatable(_):
    dff = df_train
    return dff.to_dict('records')

@app.callback(
    Output('plot-map-train', "figure"),
    Input('table', "derived_virtual_selected_rows")
)
def create_graph(selected_row_index):
    logger.info(selected_row_index)
    if (selected_row_index is None) or (selected_row_index == []):
        fig_map = {}
    else:
        fig_map = show_map_marker_lines(selected_row_index[0])
    return fig_map