from src.data_for_tool import add_distance_and_time
from src.data_matrix import create_dict_points
from src.plots import graph_solution, graph_road
from src.co2_modells import co2_modell
from dash.dependencies import Input, Output, State
from app import app, df_limited, dict_terminals, df_distance_matrix
from dash.exceptions import PreventUpdate
from loguru import logger
import pandas as pd
import datetime as dt
import json
from datetime import date

import sys
sys.path.append('../..')

df = df_limited.copy()
print(df.columns)

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

try:
    load_dicts_and_dfs
except BaseException:
    shipper = "DC1"
    start_date = "2022-01-03"
    end_date = "2022-01-04"
    df = df[(df["Delivery date"] > "2022-01-03") &
            (df["Delivery date"] < "2022-01-04")]
    clients = ['C5', 'C13', 'C15', 'C16', 'C22', 'C24', 'C27', 'C28', 'C39']
    df = df[df["Receiver name"].isin(clients)]
    dict_results, df_results_details = co2_modell(
        df, df_distance_matrix, dict_terminals, start_date, end_date, mode="intermodal")


@app.callback(
    Output('output-container-date-picker-range', 'children'),
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'))
def update_output(start_date, end_date):
    string_prefix = 'You have selected: '
    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
        start_date_string = start_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'Start Date: ' + start_date_string + ' | '
    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
        end_date_string = end_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'End Date: ' + end_date_string
    if len(string_prefix) == len('You have selected: '):
        return 'Select a date to see it displayed here'
    else:
        return string_prefix


@app.callback(
    Output('dropdown-shipper', 'options'),
    Output('dropdown-shipper', 'value'),
    Output('output-closest-dct', 'children'),
    Input('url', 'pathname'),
)
def shipper_input(_):
    logger.info(df['Shipper name'].unique())
    #shippers = [{"label": value, "value": value} for value in df['Shipper name'].unique()]
    #default_shipper = df['Shipper name'].unique()[0]
    shippers = ["DC1", "DC2"]
    default_shipper = "DC1"
    closest_dct = df_distance_matrix[default_shipper].loc[dict_terminals.keys(
    )].idxmin()
    output_closest_dct = f"Closest terminal is {closest_dct}"
    return shippers, default_shipper, output_closest_dct


@app.callback(
    Output('dropdown-terminal', 'options'),
    Output('dropdown-terminal', 'value'),
    Input('dropdown-shipper', "value")
)
def clients_input(dc):
    terminals = [{"label": value, "value": value}
                 for value in dict_terminals.keys()]
    closest_dct = df_distance_matrix[dc].loc[dict_terminals.keys()].idxmin()
    return terminals, list(dict_terminals.keys())


@app.callback(
    Output('dropdown-clients', 'options'),
    Output('dropdown-clients', 'value'),
    Input('dropdown-shipper', "value"),
    Input('dropdown-terminal', "value"),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
)
def clients_input(shipper, terminal, start_date, end_date):
    end_date = dt.datetime.strptime(
        end_date, '%Y-%m-%d') + dt.timedelta(days=1)
    df = df_limited
    logger.info(shipper)
    df = df[(df["Shipper name"] == shipper) & (df["Delivery date"]
                                               > start_date) & (df["Delivery date"] < end_date)]
    dict_points = create_dict_points(
        df,
        "Shipper name",
        "Shipper latitude",
        "Shipper longitude")
    dict_points.update(
        create_dict_points(
            df,
            "Receiver name",
            "Receiver latitude",
            "Receiver longitude"))
    logger.info(list(df['Receiver name'].unique()))
    clients = [{"label": value, "value": value}
               for value in df['Receiver name'].unique()]
    # + [{'label': 'Select all', 'value': 'all_values'}]
    # list_solution, closest_dct = create_solution(df, dict_terminals, dict_points)
    # logger.info(list_solution)
    # list_possible_clients = []
    # for i in terminal:
    #     index = int(i[-1:])-1
    #     if index < 0:
    #         index = int(i[-2:])-1
    #     logger.info(index)
    #     logger.info(list_solution)
    #     list_possible_clients.append(list_solution[index])
    # default_clients = list(df['Receiver name'].unique())
    default_clients = ["C469", "C513", "C682"]
    return clients, default_clients


@app.callback(
    Output('output-emissions-road', "children"),
    Output('output-emissions-railroad', "children"),
    Output('output-distance-road', "children"),
    Output('output-distance-railroad', "children"),
    Output('output-time-road', "children"),
    Output('output-time-railroad', "children"),
    Output('plot-co2-modell', "figure"),
    Output('plot-co2-modell-road', "figure"),
    Output('table-co2-modell', "data"),
    Input('button-execute', "n_clicks"),
    State('dropdown-shipper', "value"),
    State('dropdown-terminal', "value"),
    State('dropdown-clients', "value"),
    State('date-picker-range', 'start_date'),
    State('date-picker-range', 'end_date'),
)
def execute_co2_modell(
        n_clicks,
        shipper,
        terminal,
        clients,
        start_date,
        end_date):
    logger.info(n_clicks)
    # start_date, end_date, shipper, terminal, clients)
    df = df_limited
    logger.info(df.head())
    dict_term = dict_terminals

    logger.info(
        f"From {start_date} to {end_date} using {shipper} and {clients}")

    # dict_results_from_app = dict_results.copy()
    # df_results_details_from_app = df_results_details

    if not n_clicks:
        raise PreventUpdate
        # output_emissions_road = f'{dict_results["co2 road"]:.0f} kg CO2 eq'
        # output_emissions_railroad = f'{dict_results["co2 railroad"]:.0f} kg CO2 eq'
        # closest_dct = df_distance_matrix[shipper].loc[dict_terminals.keys()].idxmin()
        # fig = graph_solution(df, dict_results["routes railroad"], dict_terminals, closest_dct)
        # return output_emissions_road, output_emissions_railroad, fig,
        # df_results_details.to_dict('records')
    if n_clicks:
        output = f"From {start_date} to {end_date} using {shipper} and {clients}"
        logger.info(end_date)
        end_date = dt.datetime.strptime(
            end_date, '%Y-%m-%d') + dt.timedelta(days=1)
        logger.info(end_date)
        df = df[(df["Shipper name"] == shipper) & (df["Delivery date"]
                                                   > start_date) & (df["Delivery date"] < end_date)]
        if clients != "all_values":
            df = df[df["Receiver name"].isin(clients)]
        logger.info(df["Delivery date"].min())
        logger.info(df["Delivery date"].max())
        logger.info(df.shape[0])
        dict_results_new, df_results_details_new = co2_modell(
            df, df_distance_matrix, dict_term, start_date, end_date, mode="intermodal")
        logger.info(dict_results_new)
        dict_results_new = add_distance_and_time(
            dict_results_new, df_results_details_new)
        df_results_details_new = df_results_details_new[
            df_results_details_new["Rail/road"] != "Unimodal road"]
        output_emissions_road = f'{dict_results_new["co2 road"]:.0f} kg CO2 eq'
        output_emissions_railroad = f'{dict_results_new["co2 railroad"]:.0f} kg CO2 eq'
        output_distance_road = f'{dict_results_new["distance road"]/1000:,.0f} km'
        output_distance_railroad = f'{dict_results_new["distance railroad"]/1000:,.0f} km'
        output_time_road = f'{dict_results_new["time road"]:,.4f} h'
        output_time_railroad = f'{dict_results_new["time railroad"]:,.4f} h'
        closest_dct = df_distance_matrix[shipper].loc[dict_term.keys(
        )].idxmin()
        fig_rail = graph_solution(
            df,
            dict_results_new["routes railroad"],
            dict_results_new["terminal allocation"],
            dict_term,
            closest_dct)
        fig_road = graph_road(df, dict_results_new["routes road"])
        return output_emissions_road, output_emissions_railroad, output_distance_road, output_distance_railroad, output_time_road, output_time_railroad, fig_rail, fig_road, df_results_details_new.to_dict(
            'records')


@app.callback(
    Output("collapse", "is_open"),
    [Input("button-table-calculation", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
