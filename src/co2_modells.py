import sys
sys.path.append('..')
from src.distance import get_haversine_distance_latlon
from src.evaluation_multi import evaluate_solution_multi
from src.evaluation_railroad import evaluate_solution, evaluate_solution_direct, evaluate_solution_drop
from src.create_solution import create_solution, create_solution_150_20, get_closest_dct, create_solution_individual_analysis
from src.evaluation_unimodal import evaluate_cvrp
from src.cvrp_ortools import cvrp_ortools
from src.data_matrix import create_data_model, create_dict_points
from loguru import logger
import math
import pandas as pd
import time

columns_df_results = [
        "date from", "date to", "volume",
        "co2 road", "distance road", "time road","routes road", "processing time road",
        "co2 railroad", "distance railroad", "time railroad", "terminal allocation", "routes railroad", "processing time railroad",
        "co2 prehaul", "co2 terminal", "co2 mainhaul", "co2 endhaul", "co2 allroad",
        "distance prehaul", "nb lu loading", "distance mainhaul", "nb lu unloading", "distance endhaul", "distance allroad",
        "time prehaul", "time loading", "time mainhaul", "time unloading", "time endhaul", "time allroad"
]

columns_df_results_details = [
    "Rail/road",
    "Leg",
    "Route",
    "Payload",
    "Distance",
    "GHG Emissions"]


def preprocessing_modelling(df, date_from, date_to, truck_capacity, volume):
    df = df[(df["Delivery date"] >= pd.to_datetime(date_from))
            & (df["Delivery date"] <= pd.to_datetime(date_to))]
    df["Sender weight (kg)"] = df["Sender weight (kg)"] * volume
    df = df[(df["Sender weight (kg)"] > 1) & (
        df["Sender weight (kg)"] < truck_capacity)]
    date_min = df["Delivery date"].min()
    date_max = df["Delivery date"].max()
    df_new = df.groupby(['Shipper longitude',
                         'Shipper latitude',
                         'Receiver longitude',
                         'Receiver latitude',
                         'Receiver name',
                         'Shipper name'])["Sender weight (kg)"].sum().reset_index()
    #logger.info(df_new["Sender weight (kg)"].max())
    if df_new["Sender weight (kg)"].max() < truck_capacity:
        df = df_new.copy()
    logger.info(df["Sender weight (kg)"].max())
    #df["Sender weight (kg)"] = df["Sender weight (kg)"].apply(np.ceil)
    # logger.info(df.head())
    return df, date_min, date_max


def preprocessing_modelling_without_grouping(
        df, date_from, date_to, truck_capacity, volume):
    df = df[(df["Delivery date"] >= pd.to_datetime(date_from))
            & (df["Delivery date"] <= pd.to_datetime(date_to))]
    df["Sender weight (kg)"] = df["Sender weight (kg)"] * volume
    df = df[(df["Sender weight (kg)"] > 1) & (
        df["Sender weight (kg)"] < truck_capacity)]
    date_min = df["Delivery date"].min()
    date_max = df["Delivery date"].max()
    return df, date_min, date_max


def co2_modell(df, df_distance_matrix, dict_terminals, date_from, date_to,
               algorithm="base", volume=1, power="electric", country="france",
               truck_capacity=25000, nb_trucks=20, mode="combined"):
    """
    Classic co2 modell with road and railroad
    """
    # Preprocessing
    df, date_min, date_max = preprocessing_modelling(
        df, date_from, date_to, truck_capacity, volume)

    print(df.shape)
    if df.shape[0] == 0:
        print(f"No deliveries from {date_from} to {date_to}")
        return None

    else:
        # 1. Unimodal Road
        t1 = time.process_time()
        dict_points = create_dict_points(
            df, "Shipper name", "Shipper latitude", "Shipper longitude")
        dict_points.update(
            create_dict_points(
                df,
                "Receiver name",
                "Receiver latitude",
                "Receiver longitude"))
        data = create_data_model(
            df,
            df_distance_matrix,
            dict_points,
            nb_trucks,
            truck_capacity)

        logger.info(f'Weight total truck: {sum(data["demands"])}')
        logger.info(f'Weight total df: {df["Sender weight (kg)"].sum()}')
        logger.info(
            f'Weight total demand: {sum([0] + list(df["Sender weight (kg)"].astype(int)))}')

        routes_index_truck, routes_names_truck, routes_load = cvrp_ortools(
            data)
        # logger.info(routes_index_truck)
        co2_truck, distance_truck = evaluate_cvrp(
            data, routes_index_truck, details="individually")
        df_results_truck = pd.DataFrame(columns=columns_df_results_details)
        for i in range(len(routes_names_truck)):
            route_string = routes_names_truck[i][0]
            for j in range(1, len(routes_names_truck[i])):
                if routes_names_truck[i][j] != routes_names_truck[i][j - 1]:
                    route_string = route_string + \
                        "-" + routes_names_truck[i][j]
            new_record = pd.DataFrame(
                [['Unimodal road', f"Truck {i+1}",
                  route_string, routes_load[i], distance_truck[i], co2_truck[i]]],
                columns=columns_df_results_details)
            df_results_truck = pd.concat(
                [df_results_truck, new_record], ignore_index=True)
        elapsed_time_road = time.process_time() - t1
        co2_truck = sum(co2_truck)
        distance_truck = sum(distance_truck)

        # 2. Combined Railroad
        t2 = time.process_time()

        if mode == "combined":
            list_solution, closest_dct = create_solution(
                df, dict_terminals, dict_points)
        else:
            # For intermodal transport
            list_solution, closest_dct = create_solution_150_20(
                df, dict_terminals, dict_points)

        if mode == "multi":
            logger.info(list_solution)
            co2_railroad, distance_railroad, routes_names_railroad, df_results_railroad = evaluate_solution_multi(
                df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity)
            logger.info(list_solution)
        else:
            if algorithm == "base":
                co2_railroad, distance_railroad, routes_names_railroad, df_results_railroad = evaluate_solution(
                    df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity)
            elif algorithm == "drop":
                co2_railroad, distance_railroad, routes_names_railroad, list_solution = evaluate_solution_drop(
                    df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity)
                df_results_railroad = pd.DataFrame()
            else:
                list_solution, closest_dct = create_solution_individual_analysis(
                    df, dict_terminals, dict_points)
                # logger.info(list_solution)
                # logger.info(closest_dct)
                co2_railroad, distance_railroad, routes_names_railroad, df_results_railroad = evaluate_solution(
                    df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity)
#                 co2_railroad, distance_railroad, co2_rail, distance_rail, co2_prehaul, distance_prehaul, co2_endhaul, distance_endhaul = evaluate_solution_direct(
#                     df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity)
#                 df_results_railroad = pd.DataFrame()
#                 routes_names_railroad = {}

        elapsed_time_railroad = time.process_time() - t2

        df_results = pd.concat([df_results_truck, df_results_railroad])

        # Results
        print(
            "Total processing time:",
            elapsed_time_railroad +
            elapsed_time_road)
        dict_results = {"date from": date_min,
                        "date to": date_max,
                        # weight in kg
                        "weight total": df["Sender weight (kg)"].sum(),
                        "co2 road": co2_truck,
                        "distance road": distance_truck,
                        "routes road": routes_names_truck,
                        # "Auslastungsgrad trucks":(load_truck/truck_capacity)/len(routes_names_truck),
                        "processing time road": elapsed_time_road,
                        "co2 railroad": co2_railroad,
                        "distance railroad": distance_railroad,
                        "terminal allocation": list_solution,
                        "routes railroad": routes_names_railroad,
                        # "Auslastungsgrad trucks railroad":(load_truck/truck_capacity)/len(routes_names_truck),
                        "processing time railroad": elapsed_time_railroad}
        return dict_results, df_results
    

def co2_modell_direct(
        df,
        df_distance_matrix,
        dict_terminals,
        date_from,
        date_to,
        algorithm="base",
        volume=1,
        power="electric",
        country="france",
        truck_capacity=13810,
        nb_trucks=40,
        mode="combined"):
    from src.co2 import co2_truck
    """
    Co2 modell with road and railroad, individual analysis per client
    input df with unique client and unique dc
    """
    # Preprocessing
    df, date_min, date_max = preprocessing_modelling_without_grouping(
        df, date_from, date_to, truck_capacity, volume)

    print(df.shape)
    if df.shape[0] == 0:
        print(f"No deliveries from {date_from} to {date_to}")
        return None
    else:
        # 1. Unimodal Road
        t1 = time.process_time()
        total_load = df["Sender weight (kg)"].sum()
        client = df["Receiver name"].unique()[0]
        dc = df["Shipper name"].unique()[0]
        dict_points = create_dict_points(
            df, "Shipper name", "Shipper latitude", "Shipper longitude")
        dict_points.update(
            create_dict_points(
                df,
                "Receiver name",
                "Receiver latitude",
                "Receiver longitude"))
        if total_load > truck_capacity:
            data = create_data_model(
                df,
                df_distance_matrix,
                dict_points,
                nb_trucks,
                truck_capacity)
            try:
                routes_index_road, routes_names_road, _ = cvrp_ortools(data)
                co2_road, distance_road = evaluate_cvrp(
                    data, routes_index_road)
            except BaseException:
                co2_road = distance_road = 0
                routes_names_road = [[]]
        else:
            distance_dc_client = math.ceil(df_distance_matrix[dc].loc[client])
            co2_road = co2_truck(total_load, distance_dc_client)
            distance_road = distance_dc_client
            routes_names_road = [[dc, client]]
        #co2_road, distance_road = evaluate_direct(df, df_distance_matrix, truck_capacity)
        print("only truck: ", co2_road)
        elapsed_time_road = time.process_time() - t1

        # 2. Combined Railroad
        t2 = time.process_time()
        dict_points = create_dict_points(
            df, "Shipper name", "Shipper latitude", "Shipper longitude")
        dict_points.update(
            create_dict_points(
                df,
                "Receiver name",
                "Receiver latitude",
                "Receiver longitude"))
        logger.info(dict_points)

        if mode == "combined":
            list_solution, closest_dct = create_solution(
                df, dict_terminals, dict_points)
        else:
            # For intermodal transport
            list_solution, closest_dct = create_solution_150_20(
                df, dict_terminals, dict_points)
        logger.info(list_solution)
        terminal = f"T{list_solution.index([client])+1}"
        logger.info(terminal)
        co2_railroad, distance_railroad, co2_rail, distance_rail, co2_prehaul, distance_prehaul, co2_endhaul, distance_endhaul = evaluate_solution_direct(
            df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country, nb_trucks, truck_capacity)

        print("railroad: ", co2_railroad)
        elapsed_time_railroad = time.process_time() - t2

        if terminal == closest_dct:
            recommendation = "Road"
        else:
            if co2_railroad > co2_road:
                recommendation = "Road"
            elif co2_railroad < co2_road:
                recommendation = "Rail"
            else:
                recommendation = "Indifferent"

        # Results
        print(
            "Total processing time:",
            elapsed_time_railroad +
            elapsed_time_road)
        dict_results = {
            "co2 road": co2_road,
            "distance road": distance_road / 1000,
            "processing time road": elapsed_time_road,
            "co2 railroad": co2_railroad,
            "distance railroad": distance_railroad / 1000,
            "co2 mainhaul": co2_rail,
            "distance mainhaul": distance_rail / 1000,
            "co2 prehaul": co2_prehaul,
            "co2 endhaul": co2_endhaul,
            "distance prehaul": distance_prehaul / 1000,
            "distance endhaul": distance_endhaul / 1000,
            "terminal allocation": terminal,
            "haversine distance": get_haversine_distance_latlon(
                dict_points[dc],
                dict_points[client]),
            "Recommendation": recommendation}
        return dict_results

def co2_evaluation(
        df,
        df_distance_matrix,
        dict_terminals,
        date_from,
        date_to,
        algorithm="base",
        volume=1,
        power="electric",
        country="france",
        truck_capacity=13810,
        nb_trucks=40):
    """
    input list solution, output co2 railroad
    """
    t1 = time.process_time()

    # Railroad
    closest_dct = get_closest_dct(df, dict_terminals)

    if algorithm == "base":
        co2_railroad, distance_railroad, dict_routes = evaluate_solution(
            df, list_solution, dict_terminals, closest_dct, df_distance_matrix, power, country)

    elapsed_time_railroad = time.process_time() - t1
    dict_results = {"date from": df["Delivery date"].min(),
                    "date to": df["Delivery date"].max(),
                    "co2": co2_railroad,
                    "distance": distance_railroad,
                    "terminal allocation": list_solution,
                    "routes railroad": dict_routes,
                    # "Auslastungsgrad trucks railroad":(load_truck/truck_capacity)/len(routes_names_truck),
                    "processing time": elapsed_time_railroad}
    return dict_results
