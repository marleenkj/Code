from loguru import logger
import numpy as np
import math

speed_truck = 80
speed_train = 80


def co2_truck_unimodal(payload_kg, distance_m, speed_truck=speed_truck):
    """
    taking kg and meters
    returns kg co2
    """
    payload_ton = payload_kg / 1000
    distance_km = distance_m / 1000
    # k = 3.24 #kgco2 per liter diesel
    k = 3.15

    class trip_truck:
        "trip specific parameters"
        gradient_abs = 0
        speed_kmh = speed_truck
        speed_ms = (speed_kmh * 1000) / 3600
        number_of_acc_processes_per_km = 0.2
        #number_of_acc_processes_per_km = 0.12

    class truck:
        "technical parameters"
        c_air = 0.6
        #c_roll = 0.006
        c_roll = 0.0076
        front_surface = 9.795  # m2
        empty_weight_ton = 15.000  # t
        # max_capacity = 26 #t
        energy_efficiency = 0.88
        max_power = 300
        r_idle = 3
        r_full = 68
        idle_fuel_consumption_rate = 3
        max_fuel_consumption_rate = 68

    def mesoscopic_truck(truck, trip, k):

        weight_total_truck_ton = payload_ton + truck.empty_weight_ton

        # physical parameters
        rho = 1.2
        g = 9.81

        # air resistance
        p_air = (1 / 2000) * truck.c_air * rho * \
            truck.front_surface * pow(trip.speed_ms, 3)

        # rolling resistance
        p_roll = truck.c_roll * g * weight_total_truck_ton * trip.speed_ms

        # gradient resistance
        p_gradient = weight_total_truck_ton * g * trip.speed_ms * trip.gradient_abs

        # acceleration resistance
        w_inert = (0.504 / (2 * 3600)) * \
            weight_total_truck_ton * pow(trip.speed_ms, 2)

        # total energy demand
        p_drive = p_air + p_roll + p_gradient
        energy_in_kwh = (distance_km / trip.speed_kmh) * p_drive
        energy_in_kwh += trip.number_of_acc_processes_per_km * distance_km * w_inert

        # consider trucks efficiency => results in the actual energy demand
        co2 = k * (distance_km / trip.speed_kmh) * truck.r_idle + k * ((truck.r_full -
                                                                        truck.r_idle) / (truck.max_power)) * (energy_in_kwh / truck.energy_efficiency)

        return co2

    return mesoscopic_truck(truck, trip_truck, k)


def co2_truck(payload_kg, distance_m, speed_truck=speed_truck):
    """
    taking kg and meters
    returns kg co2
    """
    payload_ton = payload_kg / 1000
    distance_km = distance_m / 1000
    # k = 3.24 #kgco2 per liter diesel
    k = 3.15

    class trip_truck:
        "trip specific parameters"
        gradient_abs = 0
        speed_kmh = speed_truck
        speed_ms = (speed_kmh * 1000) / 3600
        number_of_acc_processes_per_km = 0.2
        #number_of_acc_processes_per_km = 0.12

    class truck:
        "technical parameters"
        c_air = 0.6
        #c_roll = 0.006
        c_roll = 0.0076
        front_surface = 9.795  # m2
        empty_weight_ton = 15.000  # t
        # max_capacity = 26 #t
        energy_efficiency = 0.88
        max_power = 300
        r_idle = 3
        r_full = 68
        idle_fuel_consumption_rate = 3
        max_fuel_consumption_rate = 68

    def mesoscopic_truck(truck, trip, k):

        weight_total_truck_ton = payload_ton + truck.empty_weight_ton

        # physical parameters
        rho = 1.2
        g = 9.81

        # air resistance
        p_air = (1 / 2000) * truck.c_air * rho * \
            truck.front_surface * pow(trip.speed_ms, 3)

        # rolling resistance
        p_roll = truck.c_roll * g * weight_total_truck_ton * trip.speed_ms

        # gradient resistance
        p_gradient = weight_total_truck_ton * g * trip.speed_ms * trip.gradient_abs

        # acceleration resistance
        w_inert = (0.504 / (2 * 3600)) * \
            weight_total_truck_ton * pow(trip.speed_ms, 2)

        # total energy demand
        p_drive = p_air + p_roll + p_gradient
        energy_in_kwh = (distance_km / trip.speed_kmh) * p_drive
        energy_in_kwh += trip.number_of_acc_processes_per_km * distance_km * w_inert

        # consider trucks efficiency => results in the actual energy demand
        co2 = k * (distance_km / trip.speed_kmh) * truck.r_idle + k * ((truck.r_full -
                                                                        truck.r_idle) / (truck.max_power)) * (energy_in_kwh / truck.energy_efficiency)

        return co2

    return mesoscopic_truck(truck, trip_truck, k)


def co2_train(
        payload_kg,
        distance_m,
        weights_container_kg,
        power,
        country,
        container_size="40",
        speed_train=speed_train):
    weights_container_ton = list(np.array(weights_container_kg) / 1000)
    #payload_ton = sum(weight_containers)
    nb_container = len(weights_container_ton)
    payload_ton = payload_kg / 1000
    distance_km = distance_m / 1000

    # weight_containers = [12,13,12,14,15] len = nb container
    number_of_containers = len(weights_container_ton)

    p = 0.0811  # l/kwh
    if country == "germany":
        k = 0.574  # kgco2/kwh for germany
    elif country == "france":
        k = 0.077  # kgco2/kwh for france
    else:
        k = 0.468  # kgco2/kwh for europe
    energy_per_transshipment = 4.4  # kwh per container

    class trip_train:
        "trip specific parameters"
        gradient_abs = 0
        speed_kmh = speed_train
        speed_ms = (speed_kmh * 1000) / 3600
        number_of_acc_processes_per_km = 0.2
        #number_of_acc_processes_per_km = 0.4

    if container_size == "20":
        class train():
            "technical parameters"
            c_air_car = 0.22
            c_air_loc = 0.8
            c_roll_loc = 0.003
            c_roll_car = 0.0006
            c_roll_aux_1 = 0.0005
            c_roll_aux_2 = 0.0006
            front_surface = 9
            weight_locomotive_ton = 83
            capacity_loc_cars = 30
            engine_efficiency = 0.65
            weight_car_ton = 18
            weight_container_ton = 2.250
            capacity_car_ton = 72
            capacity_car_teu = 3
            axles_per_car = 4
    else:
        class train():
            "technical parameters"
            c_air_car = 0.22
            c_air_loc = 0.8
            c_roll_loc = 0.003
            c_roll_car = 0.0006
            c_roll_aux_1 = 0.0005
            c_roll_aux_2 = 0.0006
            front_surface = 9
            weight_locomotive_ton = 83
            capacity_loc_cars = 30
            engine_efficiency = 0.65
            weight_car_ton = 26.2
            weight_container_ton = 3.780
            capacity_car_ton = 108.8
            capacity_car_teu = 2
            axles_per_car = 6

    def mesoscopic_train(train, trip, k, energy_per_transshipment):
        number_of_wagons = math.ceil(
            number_of_containers /
            train.capacity_car_teu)
        logger.info(number_of_wagons)
        number_of_trains = math.ceil(
            number_of_wagons / train.capacity_loc_cars)

        weight_total_train_ton = train.weight_locomotive_ton + train.weight_car_ton * \
            number_of_wagons + payload_ton + number_of_containers * train.weight_container_ton

        # physical parameters
        rho = 1.2
        g = 9.81

        # air resistance
        c_air = train.c_air_loc + number_of_wagons * train.c_air_car
        p_air = (1 / 2000) * c_air * rho * \
            train.front_surface * pow(trip.speed_ms, 3)

        # rolling resistance
        c_roll = train.c_roll_loc * \
            (train.weight_locomotive_ton / weight_total_train_ton)
        c_roll += train.c_roll_car * \
            ((train.weight_car_ton * number_of_wagons + payload_ton) / weight_total_train_ton)
        c_roll += (train.axles_per_car * number_of_wagons) / \
            (10 * weight_total_train_ton * g)
        c_roll += train.c_roll_aux_1 * (trip.speed_kmh / 100)
        c_roll += train.c_roll_aux_2 * pow((trip.speed_kmh / 100), 2)
        p_roll = c_roll * g * weight_total_train_ton * trip.speed_ms

        # gradient resistance
        p_gradient = weight_total_train_ton * g * trip.speed_ms * trip.gradient_abs

        # acceleration resistance
        w_inert = (0.52 / (2 * 3600)) * \
            weight_total_train_ton * pow(trip.speed_ms, 2)

        # total energy demand
        p_drive = p_air + p_roll + p_gradient
        energy_in_kwh = (distance_km / trip.speed_kmh) * p_drive
        energy_in_kwh += trip.number_of_acc_processes_per_km * distance_km * w_inert

        # consider locomotive efficiency => results in the actual energy demand
        if power == "electric":
            co2_train = k * (1 / train.engine_efficiency) * energy_in_kwh
        else:
            k = 3.15
            co2_train = p * k * (1 / train.engine_efficiency) * energy_in_kwh
        co2_transshipment = 2 * k * number_of_containers * energy_per_transshipment

        return co2_train + co2_transshipment, co2_train, co2_transshipment

    return mesoscopic_train(train, trip_train, k, energy_per_transshipment)