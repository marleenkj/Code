from src.data_matrix import df_distance_matrix_haversine, create_dict_points
import numpy as np
import sys
import pandas as pd
from math import radians, cos, sin, asin, sqrt, sqrt
import json
import requests
sys.path.append('..')

try:
    df_individual_solution = pd.read_csv(
        "../notebooks/results/direct/df_results_direct.csv")
except BaseException:
    df_individual_solution = pd.read_csv(
        "../../notebooks/results/direct/df_results_direct.csv")


def create_solution_individual_analysis(df, dict_terminals, dict_points):
    """
    Allocation based on individual analysis
    """
    # Create list solution
    clients = list(dict_points.keys())[1:]
    dc = list(dict_points.keys())[0]
    df_distance_matrix = df_distance_matrix_haversine(dict_points)
    closest_dct = df_distance_matrix[dc][dict_terminals.keys()].idxmin()
    df_individual = df_individual_solution.copy()
    df_individual = df_individual[df_individual["dc"] == dc]
    df_individual = df_individual[df_individual["client"].isin(clients)]
    df_individual["terminal allocation"] = np.where(
        df_individual["Recommendation"] == "Road",
        closest_dct,
        df_individual["terminal allocation"])
    df_individual["terminal allocation"] = np.where(
        (df_individual["distance endhaul"] > 150) & (
            df_individual["distance endhaul"] > df_individual["distance railroad"] * 0.2),
        closest_dct,
        df_individual["terminal allocation"])

    list_solution = []
    for i in dict_terminals.keys():
        list_solution_i = df_individual[df_individual["terminal allocation"] == i]["client"].to_list(
        )
        list_solution.append(list_solution_i)
    return list_solution, closest_dct


def create_solution_150_20(df, dict_terminals, dict_points):
    """
    Relaxation of 150km/20% Rule
    """
    dict_points.update(dict_terminals)
    dc = list(dict_points.keys())[0]
    df_distance_matrix = df_distance_matrix_haversine(dict_points)
    distances = df_distance_matrix.copy()[
        list(
            dict_terminals.keys())].drop(
        list(
            dict_terminals.keys()))
    distances['Dminidx'] = distances.idxmin(axis=1)
    distances['Dmin'] = distances.min(axis=1)
    closest_dct = distances.loc[dc]['Dminidx']
    closest_dct_distance = distances.loc[dc]['Dmin']

    # Create list solution
    distances = distances.drop(dc)
    list_solution = []
    for i in dict_terminals.keys():
        list_solution.append(distances[distances["Dminidx"] == i].reset_index()[
                             "index"].to_list())
    return list_solution, closest_dct


def create_solution(df, dict_terminals, dict_points):
    """
    Including 150km/20% Rule
    """
    dict_points.update(dict_terminals)
    dc = list(dict_points.keys())[0]

    # Using haversine to determine closest_dct as the crow flies
    df_distance_matrix = df_distance_matrix_haversine(dict_points)
    distances = df_distance_matrix.copy()[
        list(
            dict_terminals.keys())].drop(
        list(
            dict_terminals.keys()))
    distances['Dminidx'] = distances.idxmin(axis=1)
    distances['Dmin'] = distances.min(axis=1)
    closest_dct = distances.loc[dc]['Dminidx']
    closest_dct_distance = distances.loc[dc]['Dmin']
    print(distances[distances["Dminidx"] == closest_dct].shape)

    # Test 150km Rule:
    distances["More than 150km"] = np.where(
        distances["Dmin"] > 150000, "Yes", "No")
    distances["More than 150km"] = np.where(
        distances["Dminidx"] == closest_dct,
        "Road",
        distances["More than 150km"])

    # Preparation and Test 20% Rule:
    try:
        df_distances = pd.read_excel(
            "../data/external/intermodal_terminals/rne_terminals_distances.xlsx")
    except BaseException:
        df_distances = pd.read_excel(
            "../../data/external/intermodal_terminals/rne_terminals_distances.xlsx")
    df_distances["id_x"] = "T" + \
        (df_distances[f"facilityId_x"] + 1).astype(str)
    df_distances["Dminidx"] = "T" + \
        (df_distances[f"facilityId_y"] + 1).astype(str)
    distances = distances.reset_index().merge(df_distances[df_distances["id_x"] == closest_dct][[
        "Dminidx", "Distance"]], on=["Dminidx"], how="left").set_index('index')
    distances["Distance"] = distances["Distance"].fillna(0)
    distances["Travel distance"] = distances["Dmin"] + \
        distances["Distance"] + closest_dct_distance
    distances["More than 20%"] = np.where(
        distances["Dmin"] > distances["Travel distance"] * 0.2, "Yes", "No")
    distances["More than 20%"] = np.where(
        distances["Dminidx"] == closest_dct,
        "Road",
        distances["More than 20%"])

    # 150km Rule and 20% Rule:
    distances["Dminidx"] = np.where(
        (distances["Dmin"] > 150000) & (
            distances["Dmin"] > distances["Travel distance"] * 0.2),
        closest_dct,
        distances["Dminidx"])
    distances["Dmin"] = np.where(
        (distances["Dmin"] > 150000) & (
            distances["Dmin"] > distances["Travel distance"] * 0.2),
        closest_dct_distance,
        distances["Dmin"])
    print(distances[distances["Dminidx"] == closest_dct].shape)
    # return distances

    # Create list solution
    distances = distances.drop(dc)
    list_solution = []
    for i in dict_terminals.keys():
        list_solution.append(distances[distances["Dminidx"] == i].reset_index()[
                             "index"].to_list())
    return list_solution, closest_dct


def create_df_analysis_150_20(df, dict_terminals, dict_points):
    """
    Including 150km/20% Rule
    """
    dict_points.update(dict_terminals)
    dc = list(dict_points.keys())[0]

    # Using haversine to determine closest_dct as the crow flies
    df_distance_matrix = df_distance_matrix_haversine(dict_points)
    distances = df_distance_matrix.copy()[
        list(
            dict_terminals.keys())].drop(
        list(
            dict_terminals.keys()))
    distances['Dminidx'] = distances.idxmin(axis=1)
    distances['Dmin'] = distances.min(axis=1)
    closest_dct = distances.loc[dc]['Dminidx']
    closest_dct_distance = distances.loc[dc]['Dmin']
    print(distances[distances["Dminidx"] == closest_dct].shape)

    # Test 150km Rule:
    distances["More than 150km"] = np.where(
        distances["Dmin"] > 150000, "Yes", "No")
    #distances["More than 150km"] = np.where(distances["Dminidx"] == closest_dct, "Road", distances["More than 150km"])

    # Preparation and Test 20% Rule:
    df_distances = pd.read_excel(
        "../data/external/intermodal_terminals/rne_terminals_distances.xlsx")
    df_distances["id_x"] = "T" + \
        (df_distances[f"facilityId_x"] + 1).astype(str)
    df_distances["Dminidx"] = "T" + \
        (df_distances[f"facilityId_y"] + 1).astype(str)
    distances = distances.reset_index().merge(df_distances[df_distances["id_x"] == closest_dct][[
        "Dminidx", "Distance"]], on=["Dminidx"], how="left").set_index('index')
    distances["Distance"] = distances["Distance"].fillna(0)
    distances["Travel distance"] = distances["Dmin"] + \
        distances["Distance"] + closest_dct_distance
    distances["More than 20%"] = np.where(
        distances["Dmin"] > distances["Travel distance"] * 0.2, "Yes", "No")
    distances["More than 20%"] = np.where(
        distances["Dminidx"] == closest_dct,
        "Road",
        distances["More than 20%"])

    return distances


def sensi_distance(df, dict_terminals, df_distance_matrix, dc):
    distances = df_distance_matrix.copy()[
        list(
            dict_terminals.keys())].drop(
        list(
            dict_terminals.keys()))
    distances['Dminidx'] = distances.idxmin(axis=1)
    closest_dct = distances.loc[dc]['Dminidx']
    distances['Dmin'] = distances.min(axis=1)
    distances = distances.drop(dc)
    list_solution = []
    average_distance = []
    dict_solution = {}
    for i in dict_terminals.keys():
        dict_solution[i] = distances[distances["Dminidx"] == i].reset_index()[
            "index"].to_list()
        list_solution.append(distances[distances["Dminidx"] == i].reset_index()[
                             "index"].to_list())
        average_distance.append(
            distances[distances["Dminidx"] == i]["Dmin"].mean())
    dict_main_terminals = {}
    for i in range(len(list_solution)):
        weight = df[df["Receiver name"].isin(
            list_solution[i])]["Sender weight (kg)"].sum() / 1000
        average_distance_dc = df_distance_matrix[list_solution[i]].loc[dc].mean(
        )
        distance_dct = df_distance_matrix[f"T{i+1}"].loc[dc]
        # [Total weight, Nb clients, average distance to terminal, average distance to dc, density]
        dict_main_terminals[f"{closest_dct}-T{i+1}"] = [weight,
                                                        len(list_solution[i]),
                                                        average_distance[i],
                                                        average_distance_dc,
                                                        distance_dct]
    return list_solution, closest_dct, dict_main_terminals


def get_haversine_distance(
        x,
        shipper_name='Shipper',
        receiver_name='Receiver'):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees)
    """
    lon1, lat1 = [x[f'{shipper_name} longitude'],
                  x[f'{shipper_name} latitude']]
    lon2, lat2 = [x[f'{receiver_name} longitude'],
                  x[f'{receiver_name} latitude']]
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers. Use 3956 for miles. Determines return
    # value units.
    r = 6371
    return c * r


def create_dict_terminals(df_terminal):
    df_terminal[f"id"] = "T" + df_terminal[f"id"].astype(str)
    df_terminal["demand"] = 0
    df_terminal = df_terminal.set_index("id")
    dict_terminals = df_terminal[["longitude",
                                  "latitude", "demand"]].T.to_dict("list")
    return dict_terminals


def get_closest_dct(df_test, dict_terminals):
    def create_points_format(dict_points):
        # create points format in longitude, latitude
        list_points = list(dict_points.items())
        points = str(list_points[0][1][1]) + ',' + str(list_points[0][1][0])
        for i in range(1, len(list_points)):
            points = points + ';' + \
                str(list_points[i][1][1]) + ',' + str(list_points[i][1][0])
        return points

    point_dc = str(df_test["Shipper longitude"].iloc[0]) + \
        ',' + str(df_test["Shipper latitude"].iloc[0])
    points = create_points_format(dict_terminals)
    points = point_dc + ';' + points
    url = f'http://router.project-osrm.org/table/v1/driving/{points}?annotations=distance&sources=0'
    r = requests.get(url)
    json.loads(r.content)
    res = r.json()
    distances = res["distances"][0][1:]
    closest_dct = list(
        dict_terminals.keys())[
        distances.index(
            np.min(distances))]
    return closest_dct


def get_points_terminal(df):
    df_points = df[["Receiver name",
                    'Receiver longitude',
                    'Receiver latitude']]
    df_points.loc[-1] = df[["Terminal id", 'Terminal longitude',
                            'Terminal latitude']].iloc[1].to_list()  # adding a row
    df_points.index = df_points.index + 1  # shifting index
    df_points.sort_index(inplace=True)
    df_points = df_points.set_index("Receiver name")
    dict_points = df_points.T.to_dict("list")
    demand = [0] + df["Sender weight (kg)"].astype(int).to_list()
    return dict_points, demand


def initial_solution(df_test, df_terminal):
    # T-C routes:
    # Create all terminal-client routes and get T-C distance
    df_test['key'] = 1
    df_terminal["key"] = 1
    df_terminal_receiver = pd.merge(
        df_test,
        df_terminal,
        on='key').drop(
        "key",
        1).rename(
            columns={
                "latitude": "Terminal latitude",
                "longitude": "Terminal longitude"})
    df_terminal_receiver['Distance T-C'] = df_terminal_receiver.apply(
        lambda x: get_haversine_distance(x, "Terminal", "Receiver"), axis=1)
    # Get closest T-C terminals
    df_tc = df_terminal_receiver.iloc[df_terminal_receiver.groupby(['Receiver longitude', 'Receiver latitude'])[
        'Distance T-C'].idxmin().reset_index()['Distance T-C'].to_list()]
    df_tc = df_tc.rename({'id': 'Terminal id'}, axis=1)
    df_tc['Distance T-C harversine'] = df_tc['Distance T-C']

    dict_customer_terminal = {}
    dict_solution = {}
    list_solution = []

    for i in df_terminal["id"].to_list():
        list_solution.append(
            df_tc[df_tc["Terminal id"] == i]["Receiver name"].to_list())
        #dict_solution[f"t{i}"] = (df_tc[df_tc["Terminal id"]==i]["Receiver name"].to_list())
    return list_solution


def create_solution_old(df, dict_terminals, closest_dct):
    """
    Create initial solution, not using
    """
    dict_points = create_dict_points(
        df,
        "Shipper name",
        "Shipper latitude",
        "Shipper longitude")
    dc = list(dict_points.keys())[0]
    dict_points.update(dict_terminals)
    dict_points.update(
        create_dict_points(
            df,
            "Receiver name",
            "Receiver latitude",
            "Receiver longitude"))
    distances = create_distance_matrix(
        dict_points)[list(df["Receiver name"].unique())]
    distances = distances[~distances.index.isin(
        list(df["Receiver name"].unique()))]
    distances = distances.T
    distances['Dminidx'] = distances.idxmin(axis=1)
    distances['Dmin'] = distances.min(axis=1)
    # print(dc)
    distances["Dminidx"] = np.where(
        distances["Dminidx"] == dc,
        closest_dct,
        distances["Dminidx"])
    # distance has to be smaller than 150km luftlinie
    #distances["Dminidx"] = np.where(distances["Dmin"]>150000, closest_dct, distances["Dminidx"])
    list_solution = []
    dict_solution = {}
    for i in dict_terminals.keys():
        dict_solution[i] = distances[distances["Dminidx"] == i].reset_index()[
            "index"].to_list()
        list_solution.append(distances[distances["Dminidx"] == i].reset_index()[
                             "index"].to_list())
    return list_solution
