from loguru import logger
import numpy as np
import math

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def get_solution(data, manager, routing, solution):
    """Evaluate solution on console."""
    #print(f'Objective: {solution.ObjectiveValue()}')
    total_distance = 0
    routes_load = []
    routes = {}
    for vehicle_id in range(data['num_vehicles']):
        route_load = 0
        index = routing.Start(vehicle_id)
        nodes = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            nodes.append(node_index)
            route_load += data['demands'][node_index]
            index = solution.Value(routing.NextVar(index))
        nodes.append(0)
        routes[vehicle_id] = nodes
        routes_load.append(route_load)
    return routes

def cvrp_ortools(data):
    """Solve the CVRP problem."""
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    """
    # Add costs for each vehicle used using emission costs
    penalty = 100000000000
    for vehicle_id in range(num_vehicles):
        routing.SetFixedCostOfVehicle(penalty, vehicle_id)
    """
    
    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    # # Add Distance constraint.
    # dimension_name = 'Distance'
    # routing.AddDimension(
    #     transit_callback_index,
    #     0,  # no slack
    #     3000000,  # vehicle maximum travel distance
    #     True,  # start cumul to zero
    #     dimension_name)
    # distance_dimension = routing.GetDimensionOrDie(dimension_name)
    # distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(1)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)
    #print("Solver status: ", routing.status())

    # Return solution.
    if solution:
        dict_nodes_index = get_solution(data, manager, routing, solution)
        dict_nodes_index = dict((k, v) for k, v in dict_nodes_index.items() if len(v) > 2)
        dict_nodes_names = {}
        routes_load = []
        for i in dict_nodes_index.keys():
            dict_nodes_names[i] = [{v: k for v, k in enumerate(data["customers"])}.get(a) for a in dict_nodes_index[i]]
            loads_in_route = [data["demands"][i] for i in dict_nodes_index[i]]
            routes_load.append(sum(loads_in_route))
        return list(dict_nodes_index.values()), list(dict_nodes_names.values()), routes_load
    else:
        logger.info(solution)
        logger.info("No solution was found")