import sys
import pandas as pd
sys.path.append('..')
from src.co2 import co2_truck, co2_train
from src.data_matrix import create_data_model, create_dict_points
from src.cvrp_ortools import cvrp_ortools
from src.evaluation_unimodal import evaluate_cvrp

def evaluate_all_road(df, list_solution, df_distance_matrix, nb_trucks, truck_capacity):
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
        co2, distance = evaluate_cvrp(data_t, routes_index)    
    else:
        co2 = 0
        distance = 0 
        routes_names = [[]]
    return co2, distance, routes_names, routes_load

def evaluate_with_train(df, list_clients_terminal, dict_terminals, terminal, closest_dct, 
                        df_distance_matrix, power, country, nb_trucks, truck_capacity):
    """
    Evaluation per list solution
    """
    dict_points = create_dict_points(df, "Shipper name", "Shipper latitude", "Shipper longitude") 
    dict_points.update(create_dict_points(df, "Receiver name", "Receiver latitude", "Receiver longitude"))
    dict_points.update(dict_terminals)
    dc = list(dict_points.keys())[0]
    
    if list_clients_terminal:
        # endhaul
        # do vehicle routing from terminal i to client
        df_t = df[df["Receiver name"].isin(list_clients_terminal)]
        data_t = create_data_model(df_t, df_distance_matrix, 
                                   dict(((key, dict_points[key]) for key in [terminal] + list_clients_terminal)),
                                   nb_trucks, truck_capacity)
        routes_index, routes_names = cvrp_ortools(data_t)  
        co2_endhaul, distance_endhaul = evaluate_cvrp(data_t, routes_index)
        
        # prehaul
        # pro Container ein Transporter: kein Umschlag am Terminal, da combined
        co2_prehaul = distance_prehaul = 0
        weights_container = []
        for i in range(len(routes_index)):
            container_load = df[df["Receiver name"].isin(routes_names[i])]["Sender weight (kg)"].sum()
            distance_dc_closest_dct = df_distance_matrix.loc[closest_dct][dc]
            co2_prehaul += co2_truck(container_load, distance_dc_closest_dct)
            distance_prehaul += distance_dc_closest_dct
            weights_container.append(container_load)

        # mainhaul
        co2_train, distance_train = evaluate_rail(
            df, list_clients_terminal, terminal, closest_dct, weights_container, df_distance_matrix, power, country)

        # all together
        co2 = co2_prehaul + co2_train + co2_endhaul
        distance = distance_prehaul + distance_train + distance_endhaul
    else:
        co2 = 0
        routes_names = [[]]
        distance = 0
        
    return co2, distance, routes_names

def evaluate_rail(df, list_clients_terminal, terminal, closest_dct, nb_container, df_distance_matrix, power, country):
    """
    Evaluation rail per shipment
    """
    df_distances = pd.read_excel("../data/external/intermodal_terminals/rne_terminals_distances.xlsx")
    df_distances["id_x"]="T" + (df_distances[f"facilityId_x"]+1).astype(str)
    df_distances["id_y"]="T" + (df_distances[f"facilityId_y"]+1).astype(str)
    emissions_rail = 0
    if (list_clients_terminal):
        df_t = df[df["Receiver name"].isin(list_clients_terminal)]
        total_demand = df_t["Sender weight (kg)"].sum()
        distance_arc = df_distances[(df_distances["id_x"]==closest_dct)&(df_distances["id_y"]==terminal)]["Distance"].iloc[0]*1000
        #print(distance_arc)
        nb_container = nb_container
        emissions = co2_train(total_demand, distance_arc, nb_container, power, country)[0]
    else:
        emissions = 0
    return emissions, distance_arc

def evaluate_solution_drop(df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity):
    list_solution_of_closest_dct = list_solution[list(dict_terminals.keys()).index(closest_dct)]
    co2_dc, distance_dc, routes_names = evaluate_all_road(df, list_solution_of_closest_dct, df_distance_matrix, nb_trucks, truck_capacity)
    dict_with_train = {}
    dict_co2_old = {}
    dict_co2_old[closest_dct] = co2_dc
    dict_with_train[closest_dct] = {"co2": co2_dc, "distance": distance_dc, "routes": routes_names}
    rail_to_road_switch = True
    iterations = 0
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
        co2_dc, distance_dc, routes_names = evaluate_all_road(
            df, list_solution_of_closest_dct, df_distance_matrix, nb_trucks, truck_capacity)
        dict_routes = {}
        dict_co2[closest_dct] = co2_dc
        dict_routes[closest_dct] = routes_names
        for i in range(len(list_solution)):
            if list_solution[i]:
                terminal = list(dict_terminals.keys())[i]
                if closest_dct != terminal:
                    co2_dc_with_train = dict_with_train[terminal]["co2"] + co2_dc
                    co2_without_train, distance_without_train, routes_without_train = evaluate_all_road(
                        df, list_solution_of_closest_dct + list_solution[i], df_distance_matrix, nb_trucks, truck_capacity)
                    if co2_without_train < co2_dc_with_train:
                        print(f"For {terminal} is road is better: {co2_without_train} < {co2_dc_with_train}")
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
                        print(f"For {terminal} is train is better: {co2_dc_with_train} < {co2_without_train}")
                        co2 = dict_with_train[terminal]["co2"] 
                        distance = dict_with_train[terminal]["distance"] 
                        dict_routes[terminal] = dict_with_train[terminal]["routes"]
                        dict_co2[terminal] = co2
                        
                    co2_total += co2
                    print(distance, distance_total)
                    distance_total += distance
    if at_least_one_time_road_better == False:
        print("adding all road co2: ", co2_dc)
        co2_total += co2_dc
        distance_total += distance_dc
    if sum(list(dict_co2_old.values())) < sum(list(dict_co2.values())):
        co2_total = sum(list(dict_co2_old.values()))
    print("CO2 drop: ", sum(list(dict_co2.values())))
    print("CO2 drop: ", dict_co2)
    print("CO2 base: ", sum(list(dict_co2_old.values())))
    print("CO2 base: ", dict_co2_old)
    list_solution[list(dict_terminals.keys()).index(closest_dct)] = list_solution_of_closest_dct
    return co2_total, distance_total, dict_routes, list_solution