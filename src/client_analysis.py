import sys
sys.path.append('..')
import pandas as pd
import time
import numpy as np
from src.co2_modells import co2_modell_direct

def create_inidividual_client_analysis_table(df, dc, weight, df_distance_matrix, list_mondays, dict_terminals, ftl = "truck"):
    df = df[df["Shipper name"]==dc]
    df_individual = df.groupby(["Receiver name", "Receiver latitude", "Receiver longitude", "Shipper name", "Shipper longitude", "Shipper latitude"]).sum().reset_index()
    df_individual["Sender weight (kg)"] = weight
    df_individual["Delivery date"] = list_mondays[2]
    t = time.process_time()
    df_results_direct = pd.DataFrame(columns = ["co2 road", "distance road",
                                                "co2 railroad", "co2 mainhaul", "co2 prehaul", "co2 endhaul", 
                                                "distance railroad", "distance mainhaul", "distance prehaul", "distance endhaul",
                                                "terminal allocation", "haversine distance", "Recommendation"])
    
    for i in list(df_individual["Receiver name"].unique()):
        df_temp = df_individual[df_individual["Receiver name"]==i]
        if ftl == "train":
            df_temp = pd.concat([df_temp]*2*30).reset_index()
        dict_results = co2_modell_direct(df_temp, df_distance_matrix, 
                                         dict_terminals, list_mondays[0], list_mondays[3], algorithm = "base", volume = 1, 
                                         power = "electric", country = "france", truck_capacity = 21001, nb_trucks = 60, mode = "combined")
        df_results_direct.loc[i] = dict_results
    df_results_direct["dc"]=dc
    df_results_direct = df_results_direct.reset_index().rename({"index": "client"}, axis = 1)
    return df_results_direct

def add_recommendation(df_results_direct):
    df_results_direct["distance railroad"] = df_results_direct["distance prehaul"]+df_results_direct["distance mainhaul"]+df_results_direct["distance endhaul"]
    df_results_direct["Recommendation distance"] = np.where(df_results_direct["distance road"]<df_results_direct["distance railroad"], "Road", "Rail")
    df_results_direct["Recommendation time"] = np.where(df_results_direct["time road"]<df_results_direct["time railroad"], "Road", "Rail")
    return df_results_direct

def get_df_results_direct(df_dc1, df_dc2, df_distance_matrix, list_mondays, dict_terminals, ftl_type):
    df_results_direct_ftl_truck_dc1 = create_inidividual_client_analysis_table(df_dc1, "DC1", 21000, df_distance_matrix, list_mondays, dict_terminals, ftl = ftl_type)
    df_results_direct_ftl_truck_dc2 = create_inidividual_client_analysis_table(df_dc2, "DC2", 21000, df_distance_matrix, list_mondays, dict_terminals, ftl = ftl_type)
    df_results_direct = pd.concat([df_results_direct_ftl_truck_dc1, df_results_direct_ftl_truck_dc2]).reset_index(drop = True)
    speed_train = 80
    speed_truck = 80
    loading_terminal = 15/60 #15minutes per LU
    unloading_terminal = 10/60 #10minutes per LU
    nb_loading_units = 1
    if ftl_type == "train":
        nb_loading_units = 60
    print(nb_loading_units)
    df_results_direct["time road"] = df_results_direct["distance road"]/speed_truck
    df_results_direct["time mainhaul"] = df_results_direct["distance mainhaul"]/speed_train
    df_results_direct["time prehaul"] = df_results_direct["distance prehaul"]/speed_truck 
    df_results_direct["time endhaul"] = df_results_direct["distance endhaul"]/speed_truck
    df_results_direct["time loading"] = loading_terminal * nb_loading_units
    df_results_direct["time unloading"] = unloading_terminal * nb_loading_units
    df_results_direct["time railroad"] = df_results_direct["time mainhaul"]+df_results_direct["time prehaul"]+df_results_direct["time endhaul"]+ df_results_direct["time loading"] + df_results_direct["time unloading"]
    df_results_direct.to_csv(f"results/direct/df_results_direct_ftl_{ftl_type}_speed_{speed_train}_{speed_truck}.csv")
    df_results_direct = add_recommendation(df_results_direct)
    return df_results_direct

