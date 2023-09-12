import random
from src.co2 import co2_truck
import sys
sys.path.append('..')


def find_nearest_customer(
        data,
        current_location,
        remaining_capacity,
        remaining_customers):
    # Find the nearest customer based on the current location
    min_distance = float('inf')
    nearest_customer = None
    current_location_index = data["customers"].index(current_location)
    for customer in remaining_customers:
        customer_index = data["customers"].index(customer)
        if data["demands"][customer_index] <= remaining_capacity:
            distance = data["distance_matrix"][current_location_index][customer_index]
            if distance < min_distance:
                min_distance = distance
                nearest_customer = customer
    return nearest_customer


def construct_initial_solution(data, capacity_limit):
    # Construct an initial solution using a greedy strategy
    remaining_customers = data["customers"].copy()
    num_customers = len(remaining_customers)
    remaining_capacity = capacity_limit
    dc_name = data["customers"][0]
    solution = [[dc_name]]
    current_location = dc_name  # Starting from the depot (location 0)
    remaining_customers.remove(current_location)

    while remaining_customers:
        nearest_customer = find_nearest_customer(
            data, current_location, remaining_capacity, remaining_customers)
        if nearest_customer is None:
            # No feasible customer found with remaining capacity, end route
            solution[-1].append(dc_name)
            # start a new route
            solution.append([dc_name])
            remaining_capacity = capacity_limit
            current_location = dc_name
        else:
            nearest_customer_index = data["customers"].index(nearest_customer)
            solution[-1].append(nearest_customer)
            remaining_capacity -= data["demands"][nearest_customer_index]
            current_location = nearest_customer
            remaining_customers.remove(nearest_customer)
    solution[-1].append(dc_name)
    return solution


def evaluate_route(data, route):
    """
    calculates distance and co2 of complete route dc->client->dc
    takes input: route as list and data matrix
    """
    # get total load
    route_load = 0
    for point in route:
        route_load += data["demands"][data["customers"].index(point)]

    # Calculate the total distance of a route
    route_co2 = 0
    route_distance = 0
    current_load = route_load

    for i in range(len(route) - 1):
        distance_arc = data["distance_matrix"][data["customers"].index(
            route[i])][data["customers"].index(route[i + 1])]  # in meters
        route_distance += distance_arc
        # in kg
        current_load -= data["demands"][data["customers"].index(route[i])]
        route_co2 += co2_truck(current_load, distance_arc)
    return route_co2, route_distance


def evaluate_cvrp(data, solution):
    total_co2 = 0
    distances = []
    for route in solution:
        route_co2, route_distance = evaluate_route(data, route)
        distances.append(route_distance)
        total_co2 += route_co2
    return total_co2

# 2-opt local search
# Verbesserungsheuristik


def swap_2opt(route, i, j):
    new_route = route[:i] + route[i:j + 1][::-1] + route[j + 1:]
    return new_route


def local_search(solution):
    improved = True
    best_cost = evaluate_solution(solution)

    while improved:
        improved = False

        for r in range(len(solution)):
            route = solution[r]

            for i in range(1, len(route) - 1):
                for j in range(i + 1, len(route)):
                    new_route = swap_2opt(route, i, j)
                    new_cost = evaluate_solution(
                        solution) - evaluate_route(route) + evaluate_route(new_route)

                    if new_cost < best_cost:
                        solution[r] = new_route
                        best_cost = new_cost
                        improved = True

    return solution, best_cost


# local search with swap


def swap_customers(solution):
    capacity = 17000
    search = True
    while search:
        # Perform a random swap of two customers between two random routes
        vehicle1 = random.randint(0, len(solution) - 1)
        vehicle2 = random.randint(0, len(solution) - 1)

        if solution[vehicle1] and solution[vehicle2]:
            customer1 = random.choice(solution[vehicle1])
            customer2 = random.choice(solution[vehicle2])

            # Calculate the new solution after the swap
            new_solution = [route.copy() for route in solution]
            new_solution[vehicle1].remove(customer1)
            new_solution[vehicle1].append(customer2)
            new_solution[vehicle2].remove(customer2)
            new_solution[vehicle2].append(customer1)

        load1 = 0
        for point in new_solution[vehicle1]:
            load1 += dict_demand[point]

        load2 = 0
        for point in new_solution[vehicle2]:
            load2 += dict_demand[point]

        if load1 <= capacity and load2 <= capacity:
            search = False

    return new_solution


def local_search(solution, max_iterations):
    current_solution = solution
    best_solution = current_solution.copy()
    best_cost = evaluate_solution(solution)

    # Perform local search iterations
    for iteration in range(max_iterations):
        new_solution = swap_customers(current_solution)
        new_cost = evaluate_solution(new_solution)

        # If the new solution is an improvement, accept it
        if new_cost < best_cost:
            current_solution = new_solution.copy()
            best_solution = new_solution.copy()
            best_cost = new_cost
        else:
            pass

    return best_solution, best_cost


def swap_customers(routes):
    # Perform a random swap of customers between two random routes
    route1_index = random.randint(0, len(routes) - 1)
    route2_index = random.randint(0, len(routes) - 1)

    route1 = routes[route1_index]
    route2 = routes[route2_index]

    if len(route1) < 3 or len(route2) < 3:
        return routes

    customer1_index = random.randint(1, len(route1) - 2)
    customer2_index = random.randint(1, len(route2) - 2)

    customer1 = route1[customer1_index]
    customer2 = route2[customer2_index]

    if sum(customer1[2] for customer1 in route2) - \
            customer2[2] + customer1[2] <= capacity:
        route1[customer1_index] = customer2
        route2[customer2_index] = customer1

    return routes

# alns


def evaluate_new_solution(list_solution, terminals):
    def evaluate_road(list_solution, terminals):
        emissions_road = 0
        dc_name = list(dict_points.keys())[0]
        dict_co2_road = pd.read_csv(
            "road_emission.csv",
            index_col=0).T.to_dict("index")["emissions"]
        for i in terminals:
            if f"T{i}" == closest_dct:
                data = create_data_model(
                    dict(((key, dict_points[key]) for key in [dc_name] + list_solution[i])), 10)
            else:
                data = create_data_model(
                    dict(((key, dict_points[key]) for key in [f"T{i}"] + list_solution[i])), 10)
            routes_index, routes_names = cvrp_ortools(data)
            emissions = evaluate_cvrp(data, routes_index)
            dict_co2_road[f"T{i}"] = emissions
        emissions_road = sum(list(dict_co2_road.values()))
        pd.DataFrame.from_dict(dict_co2_road, orient="index").rename(
            {0: "emissions"}, axis=1).reset_index().to_csv("road_emission.csv", index=False)
        return emissions_road

    def evaluate_rail(list_solution):
        emissions_rail = 0
        for i in range(len(list_solution)):
            if f"T{i}" != closest_dct:
                total_demand = sum([int(item[2]) for item in list(
                    dict(((key, dict_points[key]) for key in list_solution[i])).values())])
                emissions_rail += co2_train(100, total_demand)[0]
        return emissions_rail

    emissions = 0
    emissions += evaluate_road(list_solution, terminals)
    emissions += evaluate_rail(list_solution)

    return emissions


def swap_customers(solution):
    # Perform a random swap of two customers between two random routes
    terminal1 = random.randint(0, len(solution) - 1)
    terminal2 = random.randint(0, len(solution) - 1)

    if solution[terminal1] and solution[terminal2]:
        customer1 = random.choice(solution[terminal1])
        customer2 = random.choice(solution[terminal2])

        # Calculate the new solution after the swap
        new_solution = [assignment.copy() for assignment in solution]
        new_solution[terminal1].remove(customer1)
        new_solution[terminal1].append(customer2)
        new_solution[terminal2].remove(customer2)
        new_solution[terminal2].append(customer1)

        terminals = [terminal1, terminal2]

    return new_solution, terminals


def local_search(solution, best_emissions, max_iterations):
    current_solution = solution
    best_solution = current_solution.copy()
    best_cost = best_emissions

    # Perform local search iterations
    for iteration in range(max_iterations):
        print(f"Iteration {iteration}")
        new_solution, terminals = swap_customers(current_solution)
        new_cost = evaluate_new_solution(new_solution, terminals)

        # If the new solution is an improvement, accept it
        if new_cost < best_cost:
            print("better solution")
            current_solution = new_solution.copy()
            best_solution = new_solution.copy()
            best_cost = new_cost
        else:
            print("solution is worse")

    return best_solution, best_cost
