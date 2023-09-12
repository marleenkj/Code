from src.data_matrix import create_dict_points, create_df_distance_matrix
import datetime
import calendar
from datetime import date, timedelta
import sys
import pandas as pd
sys.path.append('..')


def all_mondays(year):
    mondays = []
    first_day = date(year, 1, 1)
    if first_day.weekday() == 0:
        d = first_day
    else:
        d = first_day + timedelta(days=7 - first_day.weekday())
    while d.year == year:
        mondays.append(d)
        d += timedelta(days=7)
    return mondays


def all_wednesdays(year):
    wednesdays = []
    first_day = date(year, 1, 1)
    start_not_found = True
    while start_not_found:
        if first_day.weekday() == 2:
            d = first_day
            start_not_found = False
        else:
            first_day += timedelta(days=1)
    while d.year == year:
        wednesdays.append(d)
        d += timedelta(days=7)
    return wednesdays


def all_fridays(year):
    fridays = []
    first_day = date(year, 1, 1)
    start_not_found = True
    while start_not_found:
        if first_day.weekday() == 4:
            d = first_day
            start_not_found = False
        else:
            first_day += timedelta(days=1)
    while d.year == year:
        fridays.append(d)
        d += timedelta(days=7)
    return fridays


def create_list_days_month(year, month):
    list_days = []
    num_days = calendar.monthrange(year, month)[1]
    list_days += [datetime.date(year, month, day)
                  for day in range(1, num_days + 1)]
    return list_days


def create_list_days_week(year, month):
    list_days = []
    num_days = calendar.monthrange(year, month)[1]
    list_days += [datetime.date(year, month, day)
                  for day in range(1, num_days + 1)]
    return list_days


def create_lists_days_weeks_months(year=2022):
    # list days
    list_days = []
    for i in range(1, 13):
        month = i
        num_days = calendar.monthrange(year, month)[1]
        list_days += [datetime.date(year, month, day)
                      for day in range(1, num_days + 1)]

    # list mondays, wednesdays, fridays
    list_mondays = all_mondays(year)
    list_wednesdays = all_wednesdays(year)
    list_fridays = all_fridays(year)

    # list_bi_daily
    list_bi_daily = []
    for y in range(len(list_mondays)):
        a = list_mondays[y]
        b = list_wednesdays[y]
        c = list_fridays[y]
        temp = [a, b, c]
        list_bi_daily.extend(temp)

    # List_months
    list_months = []
    for i in range(1, 13):
        # print(i)
        d = date(year, i, 1)
        list_months.append(d)
    return list_days, list_mondays, list_bi_daily, list_months


def create_limited_dataset(df, percentage, dc="all"):
    if dc == "all":
        df_dc = df.copy()
    else:
        df_dc = df[df["Shipper name"] == dc]
    weight = df_dc.groupby(["Receiver name"])["Sender weight (kg)"].sum(
    ).reset_index().sort_values(by="Sender weight (kg)", ascending=False)
    weight["Sender weight cum"] = weight["Sender weight (kg)"].cumsum()
    high_volume_clients = weight[weight["Sender weight cum"] <
                                 df_dc["Sender weight (kg)"].sum() * percentage]["Receiver name"]
    df_dc = df_dc[df_dc["Receiver name"].isin(high_volume_clients)]
    print(len(df_dc["Receiver name"].unique()))
    return df_dc


def remove_nan_distance_matrix(df, df_distance_matrix):
    df_distance_matrix_new = df_distance_matrix.dropna(
        thresh=df_distance_matrix.isna().sum()[0] + 1,
        axis=1).dropna(
        thresh=df_distance_matrix.isna().sum()[0] + 1,
        axis=0)
    clients_to_remove = list(
        df_distance_matrix.columns.difference(
            df_distance_matrix_new.columns))
    print(clients_to_remove)
    return df_distance_matrix_new, clients_to_remove


def create_table_daily_mean(df, name):
    """
    returns GHG in kg GHG
    """
    mean_co2_road = df["co2 road"].sum() / 365
    mean_co2_rail = df["co2 railroad"].sum() / 365
    difference_absolute = mean_co2_road - mean_co2_rail
    difference_relative = (1 - (mean_co2_rail / mean_co2_road))
    df_new = pd.DataFrame(
        {name: [mean_co2_road, mean_co2_rail, difference_absolute, difference_relative]})
    return df_new


def create_table_total(df, name):
    """
    returns GHG in t GHG
    """
    total_co2_road = df["co2 road"].sum() / 1000
    print(name, ": ", total_co2_road / 365)
    total_co2_rail = df["co2 railroad"].sum() / 1000
    print(name, ": ", total_co2_rail / 365)
    difference_absolute = total_co2_road - total_co2_rail
    difference_relative = (1 - (total_co2_rail / total_co2_road))
    df_new = pd.DataFrame(
        {name: [total_co2_road, total_co2_rail, difference_absolute, difference_relative]})
    return df_new


def create_table_total_distance(df, name):
    """
    returns distance in km
    """
    total_co2_road = df["distance road"].sum()
    print(name, ": ", total_co2_road / 365)
    total_co2_rail = df["distance railroad"].sum()
    print(name, ": ", total_co2_rail / 365)
    difference_absolute = total_co2_road - total_co2_rail
    difference_relative = (1 - (total_co2_rail / total_co2_road))
    df_new = pd.DataFrame(
        {name: [total_co2_road, total_co2_rail, difference_absolute, difference_relative]})
    return df_new


def create_table_total_time(df, name):
    """
    returns distance in km
    """
    total_co2_road = df["time road"].sum()
    print(name, ": ", total_co2_road / 365)
    total_co2_rail = df["time railroad"].sum()
    print(name, ": ", total_co2_rail / 365)
    difference_absolute = total_co2_road - total_co2_rail
    difference_relative = (1 - (total_co2_rail / total_co2_road))
    df_new = pd.DataFrame(
        {name: [total_co2_road, total_co2_rail, difference_absolute, difference_relative]})
    return df_new


def data_cleaning_and_prep(df, dict_terminals):
    clients_to_remove = ["C840", "C986", "C808", "C11702"]
    df = df[~df["Receiver name"].isin(clients_to_remove)]

    df_dc2 = create_limited_dataset(df, 0.8, "DC2")
    df_dc3 = create_limited_dataset(df, 0.8, "DC3")

    df_distance_matrix = create_df_distance_matrix(
        pd.concat([df_dc2, df_dc3]), dict_terminals)
    df_distance_matrix, clients_to_remove = remove_nan_distance_matrix(
        pd.concat([df_dc2, df_dc3]), df_distance_matrix)

    df_dc2 = df_dc2[~df_dc2["Receiver name"].isin(clients_to_remove)]
    df_dc3 = df_dc3[~df_dc3["Receiver name"].isin(clients_to_remove)]

    return df_dc2, df_dc3, df_distance_matrix


def data_import():
    # Shipment dataset
    df = pd.read_csv('../data/processed/poc3.csv', parse_dates=["Pickup date"])

    # Scope France
    df = df[df["DC country"] == "France"]

    df_clients = df[['Receiver longitude', 'Receiver latitude']
                    ].drop_duplicates().reset_index()
    df_clients.index += 1
    df_clients = df_clients.reset_index().drop(["index"], axis=1).rename({
        "level_0": "Receiver name"}, axis=1)
    df_clients["Receiver name"] = "C" + df_clients["Receiver name"].astype(str)

    df_dc = df[['Shipper longitude', 'Shipper latitude',
                "DC country"]].drop_duplicates().reset_index()
    df_dc.index += 1
    df_dc = df_dc.reset_index().drop(["index"], axis=1).rename(
        {"level_0": "Shipper name"}, axis=1)
    df_dc["Shipper name"] = "DC" + df_dc["Shipper name"].astype(str)

    df = df[['Pickup date',
             'Country',
             'Sender weight (kg)',
             'Shipper longitude',
             'Shipper latitude',
             'Receiver longitude',
             'Receiver latitude']].merge(df_clients,
                                         on=['Receiver longitude',
                                             'Receiver latitude'],
                                         how="left").merge(df_dc,
                                                           on=['Shipper longitude',
                                                               'Shipper latitude'],
                                                           how="left")

    # limit to 17 tons per order
    #df = df[df["Sender weight (kg)"]<17000]

    #df = df[(df["Shipper name"]<"DC2")|(df["Shipper name"]<"DC3")]

    df = df.rename({"Pickup date": "Delivery date"}, axis=1)

    # Terminals
    df_terminal = pd.read_excel(
        '../data/external/intermodal_terminals/rne_final_terminals.xlsx').drop("id", axis=1).reset_index(drop=True)
    df_terminal.index = df_terminal.index + 1
    df_terminal = df_terminal.reset_index(names='id')
    df_terminal["id"] = "T" + df_terminal["id"].astype(str)
    dict_terminals = create_dict_points(
        df_terminal, "id", "latitude", "longitude")
    return df, df_terminal, dict_terminals


def data_for_tool():
    df, df_terminal, dict_terminals = data_import()
    df_dc2, df_dc3, df_distance_matrix = data_cleaning_and_prep(
        df, dict_terminals)
    return df_dc2, df_dc3, df_distance_matrix, dict_terminals, df_terminal


def add_distance_and_time(dict_results, df_results_details):
    speed_train = 73
    speed_truck = 83
    loading_terminal = 15 / 60  # 15minutes per LU
    unloading_terminal = 10 / 60  # 10minutes per LU
    # Distance allroad
    dict_results["distance allroad"] = df_results_details[df_results_details["Rail/road"]
                                                          == "Road"]["Distance"].sum()
    # Distance prehaul
    dict_results["distance prehaul"] = df_results_details[df_results_details["Rail/road"]
                                                          == "Prehaul"]["Distance"].sum()
    # Distance endhaul
    dict_results["distance endhaul"] = df_results_details[df_results_details["Rail/road"]
                                                          == "Endhaul"]["Distance"].sum()
    # Distance mainhaul
    dict_results["distance mainhaul"] = df_results_details[df_results_details["Rail/road"]
                                                           == "Mainhaul"]["Distance"].sum()
    # Number of loading at terminal
    dict_results["nb lu loading"] = df_results_details[df_results_details["Rail/road"]
                                                       == "Prehaul"].shape[0]
    # Number of loading at terminal
    dict_results["nb lu unloading"] = df_results_details[df_results_details["Rail/road"]
                                                         == "Endhaul"].shape[0]
    dict_results["time road"] = dict_results["distance road"] / \
        1000 / speed_truck
    dict_results["time allroad"] = dict_results["distance allroad"] / \
        1000 / speed_truck
    dict_results["time prehaul"] = dict_results["distance prehaul"] / \
        1000 / speed_truck
    dict_results["time endhaul"] = dict_results["distance endhaul"] / \
        1000 / speed_truck
    dict_results["time mainhaul"] = dict_results["distance mainhaul"] / \
        1000 / speed_train
    dict_results["time loading"] = dict_results["nb lu loading"] * \
        loading_terminal
    dict_results["time unloading"] = dict_results["nb lu unloading"] * \
        unloading_terminal
    dict_results["time railroad"] = dict_results["time allroad"] + dict_results["time prehaul"] + \
        dict_results["time endhaul"] + dict_results["time mainhaul"] + dict_results["time loading"] + dict_results["time unloading"]
    return dict_results
