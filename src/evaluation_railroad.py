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
from src.data_matrix import create_data_model, create_dict_points, create_df_distance_matrix, create_df_distance_matrix_dict_points
from src.cvrp_ortools import cvrp_ortools
from src.distance import get_distance_osrm_lat_lon_meters
from src.evaluation_unimodal import evaluate_cvrp
from src.evaluation_drop_combined import evaluate_solution_drop
from src.knapsack_problem import knapsack

columns_df_results_details = ["Rail/road", "Leg", "Route", "Payload", "Distance", "GHG Emissions"]

try:
    df_distances_rail = pd.read_excel("../data/external/intermodal_terminals/rne_terminals_distances.xlsx")
except:
    df_distances_rail = pd.read_excel("../../data/external/intermodal_terminals/rne_terminals_distances.xlsx")
df_distances_rail["id_x"]="T" + (df_distances_rail[f"facilityId_x"]+1).astype(str)
df_distances_rail["id_y"]="T" + (df_distances_rail[f"facilityId_y"]+1).astype(str)

def evaluate_rail(df, list_solution, dict_terminals, closest_dct, dict_weights_container, df_distance_matrix, power, country):
    """
    Evaluation of mainhaul rail part
    All rail parts
    Transhipment emissions included
    """
    emissions_rail = 0
    distance_rail = 0
    df_results = pd.DataFrame(columns = columns_df_results_details)
    
    for i in range(len(list_solution)):
        if (list_solution[i]):
            terminal = list(dict_terminals.keys())[i]
            if (terminal != closest_dct):
                weights_container = dict_weights_container[terminal]
                emissions_total, distance_arc, df_results = evaluate_rail_for_solution_i(
                    df, list_solution[i], terminal, closest_dct, weights_container, 
                    df_distance_matrix, power, country, df_results)
                emissions_rail += emissions_total
                distance_rail += distance_arc
        else:
            pass
    return emissions_rail, distance_rail, df_results

def evaluate_rail_for_solution_i(
    df, list_solution_i, terminal, closest_dct, weights_container, df_distance_matrix, power, country, df_results):
    """
    Evaluation of mainhaul rail part
    For terminal i
    Transhipment emissions included
    """
    df_t = df[df["Receiver name"].isin(list_solution_i)]
    total_demand = df_t["Sender weight (kg)"].sum()

    distance_arc = df_distances_rail[
        (df_distances_rail["id_x"]==closest_dct)&(df_distances_rail["id_y"]==terminal)
    ]["Distance"].iloc[0]*1000

    nb_container = len(weights_container)
    total_weight = sum(weights_container)

    # Taking into account two ways?
    emissions_total, emissions_haul, emission_trans = co2_train(
        total_demand, distance_arc, weights_container, power, country, container_size = "20")

    new_record = pd.DataFrame(
        [['Mainhaul', f"{terminal} Rail", f"{closest_dct}-{terminal}", 
          total_weight, distance_arc, emissions_haul]],
        columns=df_results.columns)
    df_results = pd.concat([df_results, new_record], ignore_index=True)
    new_record = pd.DataFrame(
        [['Terminal', f"{terminal} Load & Unload", f"{closest_dct}-{terminal}", 
          nb_container, distance_arc, emission_trans]],
        columns=df_results.columns)
    df_results = pd.concat([df_results, new_record], ignore_index=True)
    return emissions_total, distance_arc, df_results

def cvrp_routing(df, df_distance_matrix, dict_points, nb_trucks, truck_capacity):
    data_t = create_data_model(df, df_distance_matrix, dict_points, nb_trucks, truck_capacity)
    routes_index, routes_names, routes_load = cvrp_ortools(data_t)
    co2_endhaul, distance_endhaul = evaluate_cvrp(data_t, routes_index)
    return co2_endhaul, distance_endhaul, routes_names, routes_load

def evaluate_road(df, list_solution, dict_terminals, closest_dct, df_distance_matrix, nb_trucks, truck_capacity):
    """
    Evaluation of parts done by truck
    """
    dict_points = create_dict_points(df, "Shipper name", "Shipper latitude", "Shipper longitude") 
    dict_points.update(create_dict_points(df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dict_points.update(dict_terminals)
    
    dc = list(dict_points.keys())[0]
    
    co2_all = distance_all = 0
    dict_weights_container = {}
    dict_routes_names = {}
    df_results = pd.DataFrame(columns = columns_df_results_details)
    
    for i in range(len(list_solution)):
        terminal = list(dict_terminals.keys())[i]
        if list_solution[i]:
            if terminal != closest_dct:
                
                #  1. Evaluation endhaul
                df_t = df[df["Receiver name"].isin(list_solution[i])]
                data_t = create_data_model(df_t, df_distance_matrix, 
                                           dict(((key, dict_points[key]) for key in [terminal] + list_solution[i])), 
                                           nb_trucks, truck_capacity)
                routes_index, routes_names, routes_load = cvrp_ortools(data_t)
                co2_endhaul, distance_endhaul = evaluate_cvrp(data_t, routes_index, details = "individually")
                
                for i in range(len(routes_names)):
                    route_string = routes_names[i][0]
                    for j in range(1,len(routes_names[i])):
                        if routes_names[i][j] != routes_names[i][j-1]:
                            route_string = route_string+"-"+routes_names[i][j]
                    new_record = pd.DataFrame(
                        [['Endhaul', f"{terminal} Endhaul Container {i+1}", 
                          route_string, routes_load[i], distance_endhaul[i], co2_endhaul[i]]],
                        columns=columns_df_results_details)
                    df_results = pd.concat([df_results, new_record], ignore_index=True)
                
                #  2. Evaluation prehaul
                co2_prehaul = []
                distance_prehaul = []
                weights_container = []
                for i in range(len(routes_names)):
                    # evaluate prehaul without laoding unit change
                    container_load = routes_load[i]
                    distance_dc_closest_dct = math.ceil(df_distance_matrix.loc[dc][closest_dct])
                    co2_dc_closest_dct = co2_truck(container_load, distance_dc_closest_dct)
                    
                    new_record = pd.DataFrame(
                        [['Prehaul', f"{terminal} Prehaul Container {i+1}", f"{dc}-{closest_dct}", 
                          container_load, distance_dc_closest_dct, co2_dc_closest_dct]],
                        columns=df_results.columns)
                    df_results = pd.concat([df_results, new_record], ignore_index=True)
                    
                    co2_prehaul.append(co2_dc_closest_dct)
                    distance_prehaul.append(distance_dc_closest_dct)
                    weights_container.append(container_load)
                
                # Summary
                co2 = sum(co2_prehaul) + sum(co2_endhaul)
                distance = sum(distance_prehaul) + sum(distance_endhaul)
            else:
                # 3. Evaluation all road
                co2, distance, routes_names, routes_load = evaluate_all_road(
                    df, list_solution[i], df_distance_matrix, nb_trucks, truck_capacity, details = "individually")
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
            
        co2_all += co2
        distance_all += distance
        
        dict_routes_names[terminal] = routes_names
        dict_weights_container[terminal] = weights_container
        
    return co2_all, distance_all, dict_routes_names, dict_weights_container, df_results

def evaluate_all_road(df, list_solution, df_distance_matrix, nb_trucks, truck_capacity, details = "sum"):
    '''
    Evaluation of allroad parts
    list solution of closest dct
    '''
    if list_solution:
        df_t = df[df["Receiver name"].isin(list_solution)]
        dict_t_points = create_dict_points(df_t, "Shipper name", "Shipper latitude", "Shipper longitude")
        dict_t_points.update(create_dict_points(df_t, "Receiver name", "Receiver latitude", "Receiver longitude"))
        data_t = create_data_model(df_t, df_distance_matrix, dict_t_points, nb_trucks, truck_capacity)
        routes_index, routes_names, routes_load = cvrp_ortools(data_t)
        co2, distance = evaluate_cvrp(data_t, routes_index, details = details)
    else:
        if details == "sum":
            co2 = distance = routes_load = 0
            routes_names = [[]]
        else:
            co2 = [0]
            distance = [0]
            routes_load =[0]
            routes_names = [[]]
    return co2, distance, routes_names, routes_load

def evaluate_endhaul_direct(df, list_solution, df_distance_matrix, dict_points, terminal, nb_trucks, truck_capacity):
    """
    Evaluate endhaul, one container per client
    """
    co2_endhaul = distance_endhaul = nb_container = 0
    container_load = []
    
    for i in range(len(list_solution)):
        df_t = df[df["Receiver name"]==list_solution[i]]
        data_t = create_data_model(df_t, df_distance_matrix, 
                                   dict(((key, dict_points[key]) for key in [terminal] + [list_solution[i]])), 
                                   nb_trucks, truck_capacity)
        if sum(data_t["demands"]) > truck_capacity:
            # besser wäre es ein knapsack problem zu lösen
            routes_index, routes_names, routes_load = cvrp_ortools(data_t)
            co2_endhaul_i, distance_endhaul_i = evaluate_cvrp(data_t, routes_index)
        else:
            routes_names = [[terminal, list_solution[i], terminal]]
            routes_load = [sum(data_t["demands"])]
            distance_endhaul_i = df_distance_matrix.loc[terminal][list_solution[i]]
            co2_endhaul_i = co2_truck(sum(data_t["demands"]), distance_endhaul_i)
        co2_endhaul += co2_endhaul_i
        distance_endhaul += distance_endhaul_i
        
    return co2_endhaul, distance_endhaul, routes_names, routes_load

def evaluate_prehaul(df, df_distance_matrix, dc, closest_dct, terminal, routes_names, routes_load):
    """
    Evaluate prehaul, container distribution like endhaul
    """
    co2_prehaul = distance_prehaul = 0
    distance_dc_closest_dct = math.ceil(df_distance_matrix.loc[dc][closest_dct])
    for i in range(len(routes_names)):
        # falsch
        container_load = routes_load[i]
        co2_prehaul += co2_truck(container_load, distance_dc_closest_dct)
        distance_prehaul += distance_dc_closest_dct
    return co2_prehaul, distance_prehaul

def evaluate_solution(df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity):
    """
    Evaluate base scenario
    """
    # 1. evaluation of parts done by truck
    co2_truck, distance_truck, dict_routes_names, dict_weights_container, df_results = evaluate_road(
        df, list_solution, dict_terminals, closest_dct, df_distance_matrix, nb_trucks, truck_capacity)
    
    # 2. evaluation of parts done by train
    co2_rail, distance_rail, df_results_rail = evaluate_rail(
        df, list_solution, dict_terminals, closest_dct, dict_weights_container, df_distance_matrix, power, country)
    
    co2 = co2_truck + co2_rail
    distance = distance_truck + distance_rail
    df_results = pd.concat([df_results, df_results_rail], ignore_index=True)
    df_results.loc["total"] = df_results[["Distance", "GHG Emissions"]].sum(axis = 0).to_dict()
    
    return co2, distance, dict_routes_names, df_results

def evaluate_solution_direct(
    df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity):
    """
    Evaluate direct transport, nur Hinweg
    """
    dict_points = create_dict_points(df, "Shipper name", "Shipper latitude", "Shipper longitude")       
    dict_points.update(create_dict_points(df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dict_points.update(dict_terminals)
    
    dc = list(dict_points.keys())[0]
    
    dict_routes_names = {}
    dict_weights_container = {}
    co2_all = distance_all = 0
    for i in range(len(list_solution)):
        terminal = list(dict_terminals.keys())[i]
        if list_solution[i]:
            # 1. Evaluation endhaul direct
            co2_endhaul, distance_endhaul, routes_names, routes_load = evaluate_endhaul_direct(
                df, list_solution[i], df_distance_matrix, dict_points, terminal, nb_trucks, truck_capacity)

            # 2. Evaluation prehaul without laoding unit change
            co2_prehaul, distance_prehaul = evaluate_prehaul(
                df, df_distance_matrix, dc, closest_dct, terminal, routes_names, routes_load)

            co2 = co2_prehaul + co2_endhaul
            distance = distance_prehaul + distance_endhaul
            dict_weights_container[terminal] = routes_load
        else:
            co2 = distance = 0
            routes_names = [[]]
        
        # Combining prehaul + endhaul + allroad
        co2_all += co2
        distance_all += distance   
        #list_routes_names.append(routes_names)
        dict_routes_names[terminal] = routes_names
        co2_road = co2_all
        distance_road = distance_all
    
    # 3. Evaluation mainhaul rail transport
    co2_rail, distance_rail, df_results = evaluate_rail(
        df, list_solution, dict_terminals, closest_dct, dict_weights_container, df_distance_matrix, power, country)
    
    co2_all += co2_rail
    distance += distance_rail
        
    return co2_all, distance_all, co2_rail, distance_rail, co2_prehaul, distance_prehaul, co2_endhaul, distance_endhaul

def evaluate_with_train(df, list_clients_terminal, dict_terminals, terminal, closest_dct, 
                        df_distance_matrix, power, country, nb_trucks, truck_capacity):
    """
    Evaluation per list solution
    """
    dict_points = create_dict_points(df, "Shipper name", "Shipper latitude", "Shipper longitude") 
    dict_points.update(create_dict_points(df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dict_points.update(dict_terminals)
    dc = list(dict_points.keys())[0]
    df_results = pd.DataFrame(columns = columns_df_results_details)
    
    if list_clients_terminal:
        # endhaul
        # do vehicle routing from terminal i to client
        df_t = df[df["Receiver name"].isin(list_clients_terminal)]
        data_t = create_data_model(df_t, df_distance_matrix, 
                                   dict(((key, dict_points[key]) for key in [terminal] + list_clients_terminal)),
                                   nb_trucks, truck_capacity)
        routes_index, routes_names, routes_load = cvrp_ortools(data_t)  
        co2_endhaul, distance_endhaul = evaluate_cvrp(data_t, routes_index)
        
        # prehaul
        # pro Container ein Transporter: kein Umschlag am Terminal, da combined
        co2_prehaul = distance_prehaul = 0
        weights_container = []
        for i in range(len(routes_index)):
            container_load = routes_load[i]
            distance_dc_closest_dct = df_distance_matrix.loc[closest_dct][dc]
            co2_prehaul += co2_truck(container_load, distance_dc_closest_dct)
            distance_prehaul += distance_dc_closest_dct
            weights_container.append(container_load)
        
        # mainhaul
        co2_train, distance_train, df_results = evaluate_rail_for_solution_i(
            df, list_clients_terminal, terminal, closest_dct, weights_container, df_distance_matrix, power, country, df_results)

        # all together
        co2 = co2_prehaul + co2_train + co2_endhaul
        distance = distance_prehaul + distance_train + distance_endhaul
    else:
        co2 = 0
        routes_names = [[]]
        distance = 0
        
    return co2, distance, routes_names

def evaluate_solution_drop(
    df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity):
    """
    
    """
    list_solution_of_closest_dct = list_solution[list(dict_terminals.keys()).index(closest_dct)]
    co2_dc, distance_dc, routes_names, routes_load = evaluate_all_road(
        df, list_solution_of_closest_dct, df_distance_matrix, nb_trucks, truck_capacity)
    dict_with_train = {}
    dict_co2_old = {}
    dict_co2_old[closest_dct] = co2_dc
    dict_with_train[closest_dct] = {"co2": co2_dc, "distance": distance_dc, "routes": routes_names}
    
    rail_to_road_switch = True
    iterations = 0
    
    # Create dict_with_train
    for i in range(len(list_solution)):
        if list_solution[i]:
            terminal = list(dict_terminals.keys())[i]
            if closest_dct != terminal:
                co2_with_train, distance_with_train, routes_names_train = evaluate_with_train(
                    df, list_solution[i], dict_terminals, terminal, closest_dct, df_distance_matrix, 
                    power, country,nb_trucks, truck_capacity)
                dict_with_train[terminal] = {"co2": co2_with_train, "distance": distance_with_train, "routes": routes_names_train}
                dict_co2_old[terminal] = co2_with_train
                
    while rail_to_road_switch and (iterations<=3):
        co2_total = 0
        distance_total = 0
        iterations += 1
        dict_co2 = {}
        rail_to_road_switch = False 
        at_least_one_time_road_better = False
        
        co2_dc, distance_dc, routes_names, routes_load = evaluate_all_road(
            df, list_solution_of_closest_dct, df_distance_matrix, nb_trucks, truck_capacity)
        dict_routes = {}
        dict_co2[closest_dct] = co2_dc
        dict_routes[closest_dct] = routes_names
        for i in range(len(list_solution)):
            if list_solution[i]:
                terminal = list(dict_terminals.keys())[i]
                if closest_dct != terminal:
                    co2_dc_with_train = dict_with_train[terminal]["co2"] + co2_dc
                    co2_without_train, distance_without_train, routes_without_train, routes_load = evaluate_all_road(
                        df, list_solution_of_closest_dct + list_solution[i], df_distance_matrix, nb_trucks, truck_capacity)
                    if co2_without_train < co2_dc_with_train:
                        logger.info(f"Dropping {terminal}")
                        at_least_one_time_road_better = True
                        rail_to_road_switch = True
                        list_solution_of_closest_dct = list_solution_of_closest_dct + list_solution[i]
                        co2_dc = co2_without_train
                        distance_dc = distance_without_train
                        dict_routes[closest_dct] = routes_without_train
                        dict_co2[closest_dct] = co2_dc
                        dict_co2[terminal] = 0
                        list_solution[i] = []
                        dict_routes[terminal] = []
                        co2 = co2_dc
                        distance = distance_dc
                    else: 
                        
                        co2 = dict_with_train[terminal]["co2"] 
                        distance = dict_with_train[terminal]["distance"] 
                        dict_routes[terminal] = dict_with_train[terminal]["routes"]
                        dict_co2[terminal] = co2
                        
                    co2_total += co2
                    
                    distance_total += distance
    if at_least_one_time_road_better == False:
        co2_total += co2_dc
        distance_total += distance_dc
    if sum(list(dict_co2_old.values())) < sum(list(dict_co2.values())):
        co2_total = sum(list(dict_co2_old.values()))
    list_solution[list(dict_terminals.keys()).index(closest_dct)] = list_solution_of_closest_dct
    return co2_total, distance_total, dict_routes, list_solution



