from dash.dependencies import Input, Output, State
from app import app, df_limited, dict_terminals, df_distance_matrix
from dash.exceptions import PreventUpdate
from loguru import logger
import io
import dash_bootstrap_components as dbc
import pandas as pd
import datetime as dt
import calendar
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import date
import joblib

import sys
sys.path.append('../..')
from src.plots import graph_solution_with_radius
from src.create_solution import create_solution, create_solution_150_20
from src.data_matrix import create_dict_points
from src.co2_modells import co2_modell

file_path = "../../data/processed"
dc = "DC1"

def load_dicts_and_dfs(file_path):
    df_used = pd.read_csv(f"{file_path}/df_used.csv")
    df_results_details = pd.read_csv(f"{file_path}/df_results_details.csv")
    f = open(f"{file_path}/dict_results_details_combined.json", "r")
    dict_results_combined = json.load(f)
    f = open(f"{file_path}/dict_results_details_intermodal.json", "r")
    dict_results_intermodal = json.load(f) 
    f = open(f"{file_path}/dict_results_details_multimodal.json", "r")
    dict_results_multimodal = json.load(f) 
    return df_results_details, df_used, dict_results_combined, dict_results_intermodal, dict_results_multimodal

def evaluate_solution(mode, df, date_from, date_to, dict_terminals, list_terminals, volume, truck_capacity):
    df = df[(df["Delivery date"]>=pd.to_datetime(date_from))&(df["Delivery date"]<=pd.to_datetime(date_to))]
    dict_points = create_dict_points(df, "Shipper name", "Shipper latitude", "Shipper longitude")       
    dict_points.update(create_dict_points(df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    list_solution, closest_dct = create_solution(df, dict_terminals, dict_points)
    list_clients = []
    dc = "DC1"
    for i in list_terminals:
        list_clients += list_solution[i-1]
    list_solution, closest_dct = create_solution_150_20(df, dict_terminals, dict_points)
    list_clients += list_solution[int(closest_dct[-1])-1]
    list_clients += ["C316"]
    df  = df[df["Receiver name"].isin(list_clients)]
    df = df[df["Sender weight (kg)"]>5]
    close_clients = df_distance_matrix[df_distance_matrix[dc]<10000].index.to_list()
    df = df[~df["Receiver name"].isin(close_clients)]
    dict_results, df_results_details  = co2_modell(
        df, df_distance_matrix, dict_terminals, date_from, date_to, volume = volume, mode = mode, truck_capacity = truck_capacity)
    df["mode"] = mode
    df_results_details["mode"] = mode
    return dict_results, df_results_details, closest_dct, df

### Load data

try:
    list_terminals = [5]
    df_results_details, df_used, dict_results_combined, dict_results_intermodal, dict_results_multimodal = load_dicts_and_dfs(file_path)
except:
    logger.info("File not found")
    df = df_limited.copy()
    date_from = dt.date(2022, 1, 4)
    date_to = dt.date(2022, 1, 5)
    list_terminals = [5]
    truck_capacity = 13000
    volume = 30
    df = df[df["Shipper name"] == "DC1"]  
    dict_results_combined, df_results_details_combined, closest_dct, df_used_combined = evaluate_solution(
        "combined", df, date_from, date_to, dict_terminals, list_terminals, volume, truck_capacity)
    dict_results_intermodal, df_results_details_intermodal, closest_dct, df_used_intermodal = evaluate_solution(
        "intermodal", df, date_from, date_to, dict_terminals, list_terminals, volume, truck_capacity)
    dict_results_multimodal, df_results_details_multimodal, closest_dct, df_used_multimodal = evaluate_solution(
        "multimodal", df, date_from, date_to, dict_terminals, list_terminals, volume, truck_capacity)
    dict_results = {}
    list_infos = ["co2 railroad","routes railroad","terminal allocation"]
    dict_results_combined = {i: dict_results_combined[i] for i in list_infos}
    dict_results_intermodal = {i: dict_results_intermodal[i] for i in list_infos}
    dict_results_multimodal = {i: dict_results_multimodal[i] for i in list_infos}
    df_results_details = pd.concat([df_results_details_combined, df_results_details_intermodal, df_results_details_multimodal])
    df_used = pd.concat([df_used_combined, df_used_intermodal, df_used_multimodal])
    df_used.to_csv(f"{file_path}/df_used.csv", index = False)
    df_results_details.to_csv(f"{file_path}/df_results_details.csv", index = False)
    f = open(f"{file_path}/dict_results_details_combined.json", "w")
    json.dump(dict_results_combined, f)
    f = open(f"{file_path}/dict_results_details_intermodal.json", "w")
    json.dump(dict_results_intermodal, f) 
    f = open(f"{file_path}/dict_results_details_multimodal.json", "w")
    json.dump(dict_results_multimodal, f) 
    
@app.callback(
    Output('output-emissions-combined', "children"),
    Output('plot-co2-modell-combined', "figure"),
    Input('url', 'pathname'),
)
def co2_combined(_):
    closest_dct = df_distance_matrix.loc[dc][dict_terminals.keys()].idxmin()
    try:
        fig_combined = joblib.load("assets/fig_combined.pkl")
    except:
        fig_combined = graph_solution_with_radius(df_used[df_used["mode"]=="combined"], dict_results_combined["routes railroad"], dict_results_combined["terminal allocation"], dict_terminals, closest_dct, list_terminals)
        joblib.dump(fig_combined, "assets/fig_combined.pkl")
    output_emissions_combined = f'{dict_results_combined["co2 railroad"]:.0f} kg CO2 eq'
    return output_emissions_combined, fig_combined

@app.callback(
    Output('table-combined', "children"),
    Input('url', 'pathname'),
)
def table_combined(_):
    dff = df_results_details.copy()
    dff = dff[(dff["mode"]=="combined")&(dff["Rail/road"]!="Unimodal road")]
    dff = dff.drop(["mode"], axis = 1)
    return dbc.Table.from_dataframe(dff)

@app.callback(
    Output('output-emissions-intermodal', "children"),
    Output('plot-co2-modell-intermodal', "figure"),
    Input('url', 'pathname'),
)
def co2_intermodal(_):
    closest_dct = df_distance_matrix.loc[dc][dict_terminals.keys()].idxmin()
    try:
        fig_intermodal = joblib.load("assets/fig_intermodal.pkl")
    except:
        fig_intermodal = graph_solution_with_radius(df_used[df_used["mode"]=="intermodal"], dict_results_intermodal["routes railroad"], dict_results_intermodal["terminal allocation"], dict_terminals, closest_dct, list_terminals)
        joblib.dump(fig_intermodal, "assets/fig_intermodal.pkl")
    output_emissions_intermodal = f'{dict_results_intermodal["co2 railroad"]:.0f} kg CO2 eq'
    return output_emissions_intermodal, fig_intermodal

@app.callback(
    Output('table-intermodal', "children"),
    Input('url', 'pathname'),
)
def table_intermodal(_):
    dff = df_results_details.copy()
    dff = dff[(dff["mode"]=="intermodal")&(dff["Rail/road"]!="Unimodal road")]
    dff = dff.drop(["mode"], axis = 1)
    return dbc.Table.from_dataframe(dff)

@app.callback(
    Output('output-emissions-multimodal', "children"),
    Output('plot-co2-modell-multimodal', "figure"),
    Input('url', 'pathname'),
)
def execute_co2_modell(_):
    closest_dct = df_distance_matrix.loc[dc][dict_terminals.keys()].idxmin()
    fig_multimodal = graph_solution_with_radius(df_used[df_used["mode"]=="multimodal"], dict_results_multimodal["routes railroad"], dict_results_multimodal["terminal allocation"], dict_terminals, closest_dct, list_terminals)
    output_emissions_multimodal = f'{dict_results_multimodal["co2 railroad"]:.0f} kg CO2 eq'
    return output_emissions_multimodal, fig_multimodal
