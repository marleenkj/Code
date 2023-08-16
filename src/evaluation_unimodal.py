from loguru import logger
import numpy as np
import math
import requests
import time
import sys
sys.path.append('..')
from src.co2 import co2_truck
from src.knapsack_problem import knapsack

def distance_i_j(dict_points, point1, point2):
    # Create points format
    point1 = str(dict_points[point1][0])+','+str(dict_points[point1][1])
    point2 = str(dict_points[point2][0])+','+str(dict_points[point2][1])
    
    points = point1+';'+point2

    # get distance matrix with osrm
    url = f'http://router.project-osrm.org/route/v1/driving/{points}?overview=false'
    r = requests.get(url)
    json.loads(r.content)
    res = r.json()
    return res["routes"][0]["distance"]

def evaluate_route(data, route):
    """
    calculates distance and co2 of complete route dc->client->dc
    takes input: route as list and data matrix
    """
    route = [0] + route + [0]
    #print(route)
    # get total load
    route_load = 0
    for point in route:
        route_load += data["demands"][point]

    # Calculate the total distance of a route
    route_co2 = 0
    route_distance = 0
    current_load = route_load
    #print(route_load)

    for i in range(len(route) - 1):
        #print(f"from {i} to {i+1}")
        distance_arc = data["distance_matrix"][route[i]][route[i+1]] #in meters
        route_distance += distance_arc
        #print(f"Distance from {i} to {i+1}", distance_arc)
        current_load -= data["demands"][route[i]] # in kg
        #print("Load",current_load)
        route_co2 += co2_truck(current_load, distance_arc)
    #print(route_co2)
    return route_co2, route_distance, route_load

def evaluate_cvrp(data, solution, details = "sum"):
    """
    returns list with co2 per truck
    """
    total_co2 = []
    total_distance = []
    for route in solution:
        route_co2, route_distance, route_load = evaluate_route(data, route)
        route_reversed = route.copy()
        route_reversed.reverse()
        route_co2_reversed, route_distance_reversed, route_load_reversed = evaluate_route(data, route_reversed)
        if route_co2_reversed < route_co2:
            #print(f"Improvement of {route_co2 - route_reversed_co2}")
            route_co2 = route_co2_reversed
            route_distance = route_distance_reversed
            #print("reversing is better")
        #print(f"{route[0]}-{route[-1]}: {route_co2} kg Co2 with {route_load} and {route_distance}")
        total_co2.append(route_co2)
        total_distance.append(route_distance)
    if details == "sum":
        return sum(total_co2), sum(total_distance)
    else:
        return total_co2, total_distance

def evaluate_direct(df, df_distance_matrix, truck_capacity):
    """
    
    """
    dc = df["Shipper name"].unique()[0]
    client = df["Receiver name"].unique()[0]
    co2 = distance = 0
    distance_dc_client = math.ceil(df_distance_matrix[dc].loc[client])
    total_load = df["Sender weight (kg)"].sum()
    if total_load > truck_capacity:
        list_customers = df.index.to_list()
        list_weights = df["Sender weight (kg)"].to_list()
        list_index_per_truck = knapsack(list_customers, list_weights, truck_capacity)
        routes_names = []
        for i in range(len(list_index_per_truck)):
            load = df.iloc[list_index_per_truck[i]]["Sender weight (kg)"].sum()
            co2 += co2_truck(total_load, distance_dc_client)
            distance += distance_dc_client
            routes_names.append([dc, client])
    else:
        co2 = co2_truck(total_load, distance_dc_client)
        distance = distance_dc_client
        routes_names = [[dc, client]]
    
    return co2, distance

def evaluate_route_haversine(dict_points, route):
    start = time.time()
    """
    calculates distance and co2 of complete route dc->client->dc
    takes input: route as list and data matrix
    route_names
    """
    # get total load
    route_load = 0
    for point in route:
        route_load += dict_points[point][2]
    print(route_load)

    # Calculate the total distance of a route
    route_co2 = 0
    route_distance = 0
    current_load = route_load

    for i in range(len(route) - 1):
        distance_arc = distance_i_j(dict_points, route[i], route[i+1]) #in meters
        current_load -= dict_points[route[i]][2] # in kg
        route_distance += distance_arc
        route_co2 += co2_truck(current_load, int(distance_arc))
    end = time.time()
    print(end-start)
    return route_co2, route_distance

def evaluate_cvrp_haversine(dict_points, routes_names):
    total_co2 = 0
    distance = 0
    for route in routes_names:
        route_co2, route_distance = evaluate_route_haversine(dict_points, route)
        distance += route_distance
        total_co2 += route_co2
    return total_co2, distance