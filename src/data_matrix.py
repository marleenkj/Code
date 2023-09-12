from loguru import logger
import numpy as np
import math
import haversine
import requests
import json
import pandas as pd

# input to df_distance_matrix sollte ein dict(name: [latitude, longitude] sein)


def create_dict_points(df, name, latitude, longitude):
    df_latlong = df[[f"{name}", f'{latitude}',
                     f'{longitude}']].drop_duplicates()
    df_latlong = df_latlong.set_index(f"{name}")
    dict_points = df_latlong.T.to_dict("list")
    return dict_points


def osrm_matrix(list_points_all):
    # Achtung: at the moment we assume that we can transpose the matrix.
    # However, in reality the distances are not exactly the same

    # Create points format
    iterations = list(
        range(
            0,
            math.ceil(
                len(list_points_all) /
                100) *
            100,
            100))
    iterations.append(len(list_points_all))
    matrix = np.zeros(
        (len(iterations) -
         1,
         len(iterations) -
         1)).astype(object)
    for b in range(1, len(iterations)):
        print(b)
        for a in range(1, len(iterations)):
            #             if matrix[a-1][b-1] != 0:
            #                 matrix[b-1][a-1] = np.transpose(matrix[a-1][b-1])
            #             else:
            list_points = list_points_all[iterations[b - 1]:iterations[b]
                                          ] + list_points_all[iterations[a - 1]:iterations[a]]
            points = str(list_points[0][1][1]) + \
                ',' + str(list_points[0][1][0])
            for i in range(1, len(list_points)):
                points = points + ';' + \
                    str(list_points[i][1][1]) + ',' + str(list_points[i][1][0])
            sources = "0"
            for i in range(1, iterations[b] - iterations[b - 1]):
                sources = sources + ';' + str(i)
            destinations = str(iterations[b] - iterations[b - 1])
            for i in range(iterations[b] -
                           iterations[b - 1] + 1, len(list_points)):
                destinations = destinations + ';' + str(i)

            # get distance matrix with osrm
            url = f'http://router.project-osrm.org/table/v1/driving/{points}?annotations=distance&sources={sources}&destinations={destinations}'
            r = requests.get(url)
            json.loads(r.content)
            res = r.json()
            matrix[b - 1][a - 1] = res["distances"]

    row = matrix[0][0]
    for a in range(1, len(iterations) - 1):
        row = np.concatenate([row, matrix[0][a]], axis=1)
    matrix_all = row
    for i in range(1, len(iterations) - 1):
        row = matrix[i][0]
        for j in range(1, len(iterations) - 1):
            row = np.concatenate([row, matrix[i][j]], axis=1)
        matrix_all = np.concatenate([matrix_all, row], axis=0)
    return matrix_all


def create_df_distance_matrix_dict_points(dict_points):
    distance_matrix = osrm_matrix(list(dict_points.items()))
    df_distance_matrix = pd.DataFrame(
        distance_matrix, columns=list(
            dict_points.keys()), index=list(
            dict_points.keys()))
    return df_distance_matrix


def create_df_distance_matrix(df, dict_terminals):
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
    dict_points.update(dict_terminals)
    distance_matrix = osrm_matrix(list(dict_points.items()))
    df_distance_matrix = pd.DataFrame(
        distance_matrix, columns=list(
            dict_points.keys()), index=list(
            dict_points.keys()))
    return df_distance_matrix


def df_distance_matrix_haversine(dict_points):
    """
    takes (lat,lon)
    """
    distance_matrix = haversine.haversine_vector(
        list(
            dict_points.values()), list(
            dict_points.values()), comb=True) * 1000
    df_distance_matrix = pd.DataFrame(
        distance_matrix, columns=list(
            dict_points.keys()), index=list(
            dict_points.keys()))
    return df_distance_matrix


def df_distance_matrix_osrm(dict_points):
    """
    takes (lon, lat)
    """
    list_points = list(dict_points.items())
    points = str(list_points[0][1][1]) + ',' + str(list_points[0][1][0])
    for i in range(1, len(list_points)):
        points = points + ';' + \
            str(list_points[i][1][1]) + ',' + str(list_points[i][1][0])

    # get distance matrix with osrm
    url = f'http://router.project-osrm.org/table/v1/driving/{points}?annotations=distance'
    r = requests.get(url)
    json.loads(r.content)
    res = r.json()
    distance_matrix = np.array(res['distances'], dtype=int)
    df_distance_matrix = pd.DataFrame(
        distance_matrix, columns=list(
            dict_points.keys()), index=list(
            dict_points.keys()))
    return df_distance_matrix


def create_distance_matrix(dict_points):
    if len(dict_points.keys()) > 99:
        df_distance_matrix = df_distance_matrix_haversine(dict_points)
    else:
        df_distance_matrix = df_distance_matrix_osrm(dict_points)
    return df_distance_matrix


def create_data_model(
        df,
        df_distance_matrix,
        dict_points,
        num_vehicles=20,
        capacity=13810):
    """Stores the data for the problem."""
    df["Sender weight (kg)"] = df["Sender weight (kg)"].apply(np.ceil)
    data = {}
    data['customers'] = [list(dict_points.keys())[0]] + \
        list(df["Receiver name"])
    data['distance_matrix'] = np.ceil(np.array(
        df_distance_matrix[data['customers']].loc[data['customers']])).astype(int)
    data['demands'] = [0] + list(df["Sender weight (kg)"].astype(int))
    data['demand'] = np.array([0] + list(df["Sender weight (kg)"].astype(int)))
    data["capacity"] = capacity
    data['num_vehicles'] = num_vehicles
    data['vehicle_capacities'] = np.full(
        shape=data['num_vehicles'],
        fill_value=capacity,
        dtype=int)
    data['depot'] = 0
    #data['node_coord'] = np.array([dict_points[i] for i in data["customers"]])
    data["dimension"] = len(data['customers'])
    return data


def get_distance_osrm_dc_clients(dict_points) -> float:
    '''
    Getting distance with OSRM laitude longitude
    returns distance in km
    '''
    # call the OSMR API
    # get distance matrix with osrm
    list_points = list(dict_points.items())
    # for i in range(len(list_points)/100):
    points = str(list_points[0][1][1]) + ',' + str(list_points[0][1][0])
    for i in range(1, len(list_points)):
        points = points + ';' + \
            str(list_points[i][1][1]) + ',' + str(list_points[i][1][0])
    sources = "0"
    for i in range(1, len(list_points)):
        sources = sources + ';' + str(i)
    print(sources)
    destinations = str(0)
    url = f'http://router.project-osrm.org/table/v1/driving/{points}?annotations=distance&sources={sources}&destinations={destinations}'
    r = requests.get(url)
    json.loads(r.content)
    res = r.json()
    return res["distances"]
