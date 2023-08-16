from loguru import logger
import numpy as np
import math
import haversine
import requests
import json
import time

def create_dict_points(df):
    df_latlong = df[["Receiver name", 'Receiver longitude', 'Receiver latitude', "Sender weight (kg)"]]
    df_latlong.loc[-1] = df[["Shipper name",'Shipper longitude', 'Shipper latitude']].iloc[1].to_list() + [0]  # adding a row
    df_latlong.index = df_latlong.index + 1  # shifting index
    df_latlong.sort_index(inplace=True)
    df_latlong = df_latlong.set_index("Receiver name")
    dict_points = df_latlong.T.to_dict("list")
    return dict_points

def osrm_matrix(list_points_all):
    # Achtung: at the moment we assume that we can transpose the matrix. However, in reality the distances are not exactly the same
    
    # Create points format
    iterations = list(range(0, math.ceil(len(list_points_all)/100)*100, 100))
    iterations.append(len(list_points_all))
    matrix = np.zeros((len(iterations)-1, len(iterations)-1)).astype(object)
    for b in range(1, len(iterations)):
        print(b)
        for a in range(1, len(iterations)):
#             if matrix[a-1][b-1] != 0:
#                 matrix[b-1][a-1] = np.transpose(matrix[a-1][b-1])
#             else:
            list_points = list_points_all[iterations[b-1]:iterations[b]] + list_points_all[iterations[a-1]:iterations[a]]
            points = str(list_points[0][1][1])+','+str(list_points[0][1][0])
            for i in range(1, len(list_points)):
                points = points+';'+str(list_points[i][1][1])+','+str(list_points[i][1][0])
            sources = "0"
            for i in range(1,iterations[b]-iterations[b-1]):
                sources = sources +';'+str(i)
            destinations = str(iterations[b]-iterations[b-1])
            for i in range(iterations[b]-iterations[b-1]+1,len(list_points)):
                destinations = destinations+';'+str(i)

            # get distance matrix with osrm
            url = f'http://router.project-osrm.org/table/v1/driving/{points}?annotations=distance&sources={sources}&destinations={destinations}'
            r = requests.get(url)
            json.loads(r.content)
            res = r.json()
            matrix[b-1][a-1] = res["distances"]

    row = matrix[0][0]
    for a in range(1,len(iterations)-1):
        row = np.concatenate([row,matrix[0][a]], axis = 1)
    matrix_all = row
    for i in range(1,len(iterations)-1):
        row = matrix[i][0]
        for j in range(1,len(iterations)-1):
            row = np.concatenate([row,matrix[i][j]], axis = 1)
        matrix_all = np.concatenate([matrix_all,row], axis = 0)
    return matrix_all

def create_distance_matrix(dict_points, method):
    start = time.time()
    # create points format
    list_points = list(dict_points.items())
    if method == "haversine":
        distance_matrix = haversine.haversine_vector(list(dict_points.values()), list(dict_points.values()), comb=True)*1000
        end = time.time()
        print(f"{end - start} seconds")
        return distance_matrix.astype(int)
    if len(list_points)>100:
        distance_matrix = osrm_matrix(list_points)
        end = time.time()
        print(f"{end - start} seconds")
        return distance_matrix.astype(int)
    else: 
        # Create points format
        points = str(list_points[0][1][0])+','+str(list_points[0][1][1])
        for i in range(1, len(list_points)):
            points = points+';'+str(list_points[i][1][0])+','+str(list_points[i][1][1])

        # get distance matrix with osrm
        url = f'http://router.project-osrm.org/table/v1/driving/{points}?annotations=distance'
        r = requests.get(url)
        json.loads(r.content)
        res = r.json()
        end = time.time()
        print(f"{end - start} seconds")
        return np.array(res['distances'], dtype=int)

def create_data_model(dict_points, num_vehicles, method):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = create_distance_matrix(dict_points, method)
    data['demands'] = [int(item[2]) for item in list(dict_points.values())]
    capacity = 17000
    data['num_vehicles'] = num_vehicles
    data['vehicle_capacities'] = np.full(shape=data['num_vehicles'],fill_value=capacity,dtype=int)
    data['depot'] = 0
    data['customers'] = list(dict_points.keys())
    return data
