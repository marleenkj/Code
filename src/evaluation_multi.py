from loguru import logger
import numpy as np
import math
import haversine
import sys
import pandas as pd
from math import radians, cos, sin, asin, sqrt, atan2, sqrt, degrees, modf
import json
import time
import requests
import itertools
sys.path.append('..')
from src.co2 import co2_truck, co2_train
from src.data_matrix import create_data_model, create_distance_matrix, create_dict_points, create_df_distance_matrix
from src.cvrp_ortools import cvrp_ortools
from src.distance import get_distance_osrm_lat_lon_meters
from src.evaluation_unimodal import evaluate_cvrp
from src.evaluation_railroad import evaluate_rail, evaluate_all_road, evaluate_solution_drop
from src.create_solution import create_solution_150_20
from src.data_matrix import create_data_model, create_dict_points, create_df_distance_matrix, create_df_distance_matrix_dict_points
from src.distance import get_distance_osrm_lat_lon_meters
from src.evaluation_unimodal import evaluate_cvrp
from src.knapsack_problem import knapsack

columns_df_results_details = ["Rail/road", "Leg", "Route", "Payload", "Distance", "GHG Emissions"]

def preprocessing_modelling(df, date_from, date_to, truck_capacity, volume):
    df = df[(df["Delivery date"]>=pd.to_datetime(date_from))&(df["Delivery date"]<=pd.to_datetime(date_to))]
    df["Sender weight (kg)"] = df["Sender weight (kg)"]*volume
    df = df[(df["Sender weight (kg)"]>1)&(df["Sender weight (kg)"]<truck_capacity)]
    date_min = df["Delivery date"].min()
    date_max = df["Delivery date"].max()
    df_new = df.groupby(['Shipper longitude','Shipper latitude','Receiver longitude',
        'Receiver latitude','Receiver name', 'Shipper name'])["Sender weight (kg)"].sum().reset_index()
    #logger.info(df_new["Sender weight (kg)"].max())
    if df_new["Sender weight (kg)"].max() < truck_capacity:
        df = df_new.copy()
    logger.info(df["Sender weight (kg)"].max())
    #logger.info(df.head())
    return df, date_min, date_max

def evaluate_prehaul_multi(df, list_solution, dict_terminals, closest_dct, df_distance_matrix, truck_capacity, nb_trucks):
    """
    evaluate prehaul with loading unit change
    """
    dict_points = create_dict_points(df, "Shipper name", "Shipper latitude", "Shipper longitude")
    dict_points.update(create_dict_points(df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dict_points.update(dict_terminals)
    
    dc = list(dict_points.keys())[0]
    
    co2_all = distance_all = 0
    df_results = pd.DataFrame(columns = columns_df_results_details)
    
    # 1. Evaluate prehaul
    list_solution_no_dc = list_solution.copy()
    list_solution_no_dc[list(dict_terminals.keys()).index(closest_dct)] = []
    list_solution_flattened = list(itertools.chain(*list_solution_no_dc))
    list_customers = df[df["Receiver name"].isin(list_solution_flattened)]["Receiver name"].to_list()
    list_weights = df[df["Receiver name"].isin(list_solution_flattened)]["Sender weight (kg)"].to_list()
    
    df_t = df[df["Receiver name"].isin(list_solution_flattened)]
    data_t = create_data_model(df_t, df_distance_matrix, 
                               dict(((key, dict_points[key]) for key in [dc] + list_customers)), 
                               nb_trucks, truck_capacity)
    routes_index, routes_names, routes_load = cvrp_ortools(data_t)
    
    distance_prehaul = df_distance_matrix.loc[dc][closest_dct]
    for i in range(len(routes_names)):
        co2 = co2_truck(routes_load[i], distance_prehaul)
        route_string = routes_names[i][0]
        for j in range(1,len(routes_names[i])):
            if routes_names[i][j] != routes_names[i][j-1]:
                route_string = route_string+"-"+routes_names[i][j]
        new_record = pd.DataFrame(
            [['Railroad', f"Prehaul Container {i+1}", route_string, routes_load[i], distance_prehaul, co2]],
            columns=columns_df_results_details)
        df_results = pd.concat([df_results, new_record], ignore_index=True)
        co2_all += co2
        distance_all += distance_prehaul
    return co2_all, distance_all, df_results

def evaluate_multi_premainhaul(
    df, df_distance_matrix, dict_terminals, list_solution, date_from, date_to, power, country, truck_capacity, nb_trucks):
    """
    input: df filtered by one dc
    """
    # 0. Allocation to terminals
    dict_points = create_dict_points(df, "Shipper name", "Shipper latitude", "Shipper longitude")       
    dict_points.update(create_dict_points(df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    
    list_solution_dc, closest_dct = create_solution_150_20(df, dict_terminals, dict_points)

    list_solution_new = list_solution_dc.copy()
    list_solution_new[list(dict_terminals.keys()).index(closest_dct)] = []
    list_solution_of_closest_dct = list_solution_dc[list(dict_terminals.keys()).index(closest_dct)]

    for i in range(len(list_solution_new)):
        list_solution[i] = list_solution[i] + list_solution_new[i]

    # 1. Evaluation prehaul
    co2_prehaul, distance_prehaul, df_results_prehaul = evaluate_prehaul_multi(
        df, list_solution_new, dict_terminals, closest_dct, df_distance_matrix, truck_capacity, nb_trucks)

    # 2. Evaluation allroad
    df_results_allroad = pd.DataFrame(columns = columns_df_results_details)  
    co2_allroad, distance_allroad, routes_names, routes_load = evaluate_all_road(
        df, list_solution_of_closest_dct, df_distance_matrix, nb_trucks, truck_capacity, details = "individually")
    
    for i in range(len(routes_names)):
        route_string = routes_names[i][0]
        for j in range(1,len(routes_names[i])):
            route_string = route_string+"-"+routes_names[i][j]
        new_record = pd.DataFrame(
            [['Road', f'Truck {i+1}', route_string, routes_load[i], distance_allroad[i], co2_allroad[i]]],
            columns=columns_df_results_details)
        df_results_allroad = pd.concat([df_results_allroad, new_record], ignore_index=True)
        co2_allroad = sum(co2_allroad)
        distance_allroad = sum(distance_allroad)

    # 3. Evaluation mainhaul
    dict_nb_container = dict_weights_container = {}
    for i in range(len(list_solution_new)):
        if list_solution_new[i]:
            list_customers = df[df["Receiver name"].isin(list_solution_new[i])]["Receiver name"].to_list()
            list_weights = df[df["Receiver name"].isin(list_solution_new[i])]["Sender weight (kg)"].to_list()
            trucks_and_clients = knapsack(list_customers, list_weights, truck_capacity)
            weights_container = []
            for container in trucks_and_clients:
                load = df[df["Receiver name"].isin(container)]["Sender weight (kg)"].sum()
                weights_container.append(load)
            dict_weights_container[f"T{i+1}"] = weights_container
        else:
            dict_weights_container[f"T{i+1}"] = []

    co2_rail, distance_rail, df_results_rail = evaluate_rail(
        df, list_solution_new, dict_terminals, closest_dct, dict_weights_container, df_distance_matrix, power, country)

    distance = distance_rail+distance_allroad+distance_prehaul
    co2 = co2_prehaul+co2_allroad+co2_rail
    df_results = pd.concat([df_results_allroad, df_results_rail, df_results_prehaul], ignore_index=True)
    
    return co2, distance, list_solution, df_results

def cvrp_routing(df, df_distance_matrix, dict_points, nb_trucks, truck_capacity):
    data = create_data_model(df, df_distance_matrix, dict_points, nb_trucks, truck_capacity)
    routes_index, routes_names, routes_load = cvrp_ortools(data)
    co2_endhaul, distance_endhaul = evaluate_cvrp(data, routes_index, details = "individually")
    return co2_endhaul, distance_endhaul, routes_names, routes_load

def evaluate_endhaul_multi(df_combined, solution_terminal, dict_terminals, terminal, df_distance_matrix, nb_trucks, truck_capacity):
    df_t = df_combined[df_combined["Receiver name"].isin(solution_terminal)]
    dict_points_t = {f"{terminal}": dict_terminals[terminal]}

    co2_endhaul, distance_endhaul, routes_names, routes_load = cvrp_routing(
        df_t, df_distance_matrix, dict_points_t, nb_trucks, truck_capacity)

    df_results_endhaul = pd.DataFrame(columns = columns_df_results_details)

    for i in range(len(routes_names)):
        route_string = routes_names[i][0]
        for j in range(1,len(routes_names[i])):
            route_string = route_string+"-"+routes_names[i][j]
        new_record = pd.DataFrame(
            [['Railroad', f"{terminal} Endhaul Container {i+1}", route_string, 
              routes_load[i], distance_endhaul[i], co2_endhaul[i]]],
            columns=columns_df_results_details)
        df_results_endhaul = pd.concat([df_results_endhaul, new_record], ignore_index=True)
    co2_endhaul = sum(co2_endhaul)
    distance_endhaul = sum(distance_endhaul)
    return co2_endhaul, distance_endhaul, df_results_endhaul

def co2_modell_multi(dcs, df_combined, df_distance_matrix, dict_terminals, date_from, date_to, 
                     algorithm = "base", volume = 1, power = "electric", country = "france", 
                     truck_capacity = 30000, nb_trucks = 10):
    """
    Combining endhaul for the two dcs, requirement: multimodal transport
    """
    t1 = time.process_time()
    dict_results = {}
    distance = co2 = 0
    list_solution = [[] for key in list(dict_terminals.keys())]
    df_combined, date_min, date_max = preprocessing_modelling(df_combined, date_from, date_to, truck_capacity, volume)
    # Allocation to terminals + Evaluate prehaul, allroad, and mainhaul seperately
    df_results_premainhaul = pd.DataFrame(columns = columns_df_results_details)

    for dc in dcs:
        # Data prep
        df = df_combined[df_combined["Shipper name"]==dc]
        if df.shape[0] == 0:
            print(f"No deliveries from {date_from} to {date_to}")
        else:
            co2_dc, distance_dc, list_solution, df_results = evaluate_multi_premainhaul(
                df, df_distance_matrix, dict_terminals, list_solution, date_from, date_to, power, country, truck_capacity, nb_trucks)
            df_results["DC"] = dc
            df_results_premainhaul = pd.concat([df_results_premainhaul, df_results], ignore_index=True)
            co2 += co2_dc
            distance += distance_dc
        
    # 4. Evaluation endhaul together
    df_results_endhaul = pd.DataFrame(columns = columns_df_results_details)
    list_rail = list_solution.copy()
    co2_endhaul_all = distance_endhaul_all = 0
    df_results_endhaul_all = pd.DataFrame()
    for i in range(len(list_rail)):
        if list_rail[i]:
            solution_terminal = list_rail[i]
            terminal = list(dict_terminals.keys())[i]
            co2_endhaul, distance_endhaul, df_results_endhaul = evaluate_endhaul_multi(
                df_combined, solution_terminal, dict_terminals, terminal, 
                df_distance_matrix, nb_trucks, truck_capacity)
            co2_endhaul_all += co2_endhaul
            distance_endhaul_all += distance_endhaul
            df_results_endhaul_all = pd.concat([df_results_endhaul_all, df_results_endhaul])
            
    # Combining values for dataframe
    elapsed_time = time.process_time() - t1
    distance += distance_endhaul_all
    co2 += co2_endhaul_all
    df_results = pd.concat([df_results_endhaul_all, df_results_premainhaul], ignore_index=True)
    
    #return date_min, date_max, co2, distance, df_results
    dict_results = {
        "date from":date_min,
        "date to":date_max,
        "co2": co2, 
        "distance": distance, 
        "processing time": elapsed_time,
        "df shape": df_combined.shape[0]
    }
    return dict_results, df_results

def evaluate_solution_multi(df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity):
    """
    Evaluate base scenario
    """
    logger.info(closest_dct)
    logger.info(list_solution)
    dict_points = create_dict_points(df, "Shipper name", "Shipper latitude", "Shipper longitude")       
    dict_points.update(create_dict_points(df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dict_points.update(dict_terminals)
    # 1. Evaluation prehaul
    co2_prehaul, distance_prehaul, df_results = evaluate_prehaul_multi(
        df, list_solution, dict_terminals, closest_dct, df_distance_matrix, truck_capacity, nb_trucks)
    
    # 2. Evaluation mainhaul
    dict_weights_container = {}
    dict_routes_names = {}
    co2_all = co2_prehaul
    logger.info(co2_all)
    distance_all = distance_prehaul
    for i in range(len(list_solution)):
        terminal = list(dict_terminals.keys())[i]
        if list_solution[i]:
            solution_terminal = list_solution[i]
            if terminal != closest_dct:
                #  1a. Evaluation endhaul
                df_t = df[df["Receiver name"].isin(solution_terminal)]
                data_t = create_data_model(df_t, df_distance_matrix, 
                                           dict(((key, dict_points[key]) for key in [terminal] + solution_terminal)), 
                                           nb_trucks, truck_capacity)
                routes_index, routes_names, routes_load = cvrp_ortools(data_t)
                co2, distance = evaluate_cvrp(data_t, routes_index, details = "individually")
                dict_weights_container[terminal] = routes_load
                
                for i in range(len(routes_names)):
                    route_string = routes_names[i][0]
                    for j in range(1,len(routes_names[i])):
                        if routes_names[i][j] != routes_names[i][j-1]:
                            route_string = route_string+"-"+routes_names[i][j]
                    new_record = pd.DataFrame(
                        [['Railroad', f"{terminal} Endhaul Container {i+1}", 
                          route_string, routes_load[i], distance[i], co2[i]]],
                        columns=columns_df_results_details)
                    df_results = pd.concat([df_results, new_record], ignore_index=True)
                co2 = sum(co2)
                distance = sum(distance)
            else:
                # 1b. Evaluation all road
                co2, distance, routes_names, routes_load = evaluate_all_road(
                    df, solution_terminal, df_distance_matrix, nb_trucks, truck_capacity, details = "individually")
                for i in range(len(routes_names)):
                    route_string = routes_names[i][0]
                    for j in range(1,len(routes_names[i])):
                        route_string = route_string+"-"+routes_names[i][j]
                    new_record = pd.DataFrame(
                        [['Road', f'Truck {i+1}', route_string, routes_load[i], distance[i], co2[i]]],
                        columns=df_results.columns)
                    df_results = pd.concat([df_results, new_record], ignore_index=True)
                co2 = sum(co2)
                distance = sum(distance)
                weights_container = 0
        else:
            co2 = distance = weights_container = 0
            routes_names = [[]]
        
        dict_routes_names[terminal] = routes_names    
        co2_all += co2
        distance_all += distance
        logger.info(co2_all)
        
    co2_rail, distance_rail, df_results_rail = evaluate_rail(
        df, list_solution, dict_terminals, closest_dct, dict_weights_container, df_distance_matrix, power, country)
    
    df_results = pd.concat([df_results, df_results_rail], ignore_index=True)
    co2_all += co2_rail
    logger.info(co2_all)
    distance_all += distance_rail
    df_results.loc["total"] = df_results[["Distance", "GHG Emissions"]].sum(axis = 0).to_dict()
    
    return co2_all, distance_all, dict_routes_names, df_results