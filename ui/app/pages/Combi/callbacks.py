from dash.dependencies import Input, Output, State
from app import app, df_limited, dict_terminals, df_distance_matrix
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
from src.plots import graph_solution, graph_road, graph_solution_with_radius
from src.create_solution import create_solution, create_solution_150_20
from src.data_matrix import create_dict_points
from src.co2_modells import co2_modell

def evaluate_solution(df, date_from, date_to, dict_terminals, list_terminals, volume, truck_capacity):
    df = df[(df["Delivery date"]>=pd.to_datetime(date_from))&(df["Delivery date"]<=pd.to_datetime(date_to))]
    dict_points = create_dict_points(df, "Shipper name", "Shipper latitude", "Shipper longitude")       
    dict_points.update(create_dict_points(df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    list_solution, closest_dct = create_solution(df, dict_terminals, dict_points)
    list_clients = []
    for i in list_terminals:
        list_clients += list_solution[i-1]
    list_solution, closest_dct = create_solution_150_20(df, dict_terminals, dict_points)
    list_clients += list_solution[int(closest_dct[-1])-1]
    df  = df[df["Receiver name"].isin(list_clients)]
    df = df[df["Sender weight (kg)"]>5]
    close_clients = df_distance_matrix[df_distance_matrix["DC1"]<10000].index.to_list()
    df = df[~df["Receiver name"].isin(close_clients)]
    dict_results, df_results_details  = co2_modell(
        df, df_distance_matrix, dict_terminals, date_from, date_to, volume = volume, truck_capacity = truck_capacity)
    return dict_results, df_results_details, closest_dct, df

try:
    
except:
    df = df_limited.copy()
    date_from = dt.date(2022, 1, 4)
    date_to = dt.date(2022, 1, 5)
    list_terminals = [5]
    truck_capacity = 13000
    volume = 30
    df = df[df["Shipper name"] == "DC1"] 
    dict_results, df_results_details, closest_dct, df_used = evaluate_solution(
        df, date_from, date_to, dict_terminals, list_terminals, volume, truck_capacity)
    logger.info(dict_results)
    df_results_details.to_csv("../../notebooks/results/evaluation/evaluate_road_vs_rail.csv")

@app.callback(
    Output('output-emissions-road-eval', "children"),
    Output('output-emissions-railroad-eval', "children"),
    Output('plot-co2-modell-road-eval', "figure"),
    Output('plot-co2-modell-railroad-eval', "figure"),
    Input('url', 'pathname'),
)
def execute_co2_modell(_):
    df = df_used
    output_emissions_road = f'{dict_results["co2 road"]:.0f} kg CO2 eq'
    output_emissions_railroad = f'{dict_results["co2 railroad"]:.0f} kg CO2 eq'
    fig_road = graph_road(df, dict_results["routes road"])
    #fig_railroad = graph_solution_with_radius(df, dict_results["routes railroad"], dict_results["terminal allocation"], dict_terminals, closest_dct, list_terminals)
    fig_railroad = graph_solution(df, dict_results["routes railroad"], dict_results["terminal allocation"], dict_terminals, closest_dct)
    return output_emissions_road, output_emissions_railroad, fig_road, fig_railroad