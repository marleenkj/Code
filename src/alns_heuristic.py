import matplotlib.pyplot as plt
import matplotlib
import plotly.graph_objects as go
import numpy as np
import sys
sys.path.append('..')

# %matplotlib inline
#SEED = 1234

def plot_solution(solution, name="CVRP solution"):
    """
    Plot the routes of the passed-in solution.
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    cmap = matplotlib.cm.rainbow(np.linspace(0, 1, len(solution.routes)))

    for idx, route in enumerate(solution.routes):
        ax.plot(
            [data["node_coord"][loc][0] for loc in [0] + route + [0]],
            [data["node_coord"][loc][1] for loc in [0] + route + [0]],
            color=cmap[idx],
            marker='.'
        )

    # Plot the depot
    kwargs = dict(label="Depot", zorder=3, marker="*", s=750)
    ax.scatter(*data["node_coord"][0], c="tab:red", **kwargs)

    ax.set_title(f"{name}\n Total distance: {solution.cost}")
    ax.set_xlabel("X-coordinate")
    ax.set_ylabel("Y-coordinate")
    ax.legend(frameon=False, ncol=3)


def show_map(solution):
    dict_new = {}
    for i in solution[0]:
        dict_new[i] = dict_points[i]

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(lat=[dict_points[solution[0][0]][0]], lon=[
                  dict_points[solution[0][0]][1]], mode='markers+lines', marker={'size': 8}))
    for i in range(len(solution)):
        list_route = []
        for j in solution[i]:
            list_route.append(dict_points[j])
        fig.add_trace(
            go.Scattermapbox(
                lat=[
                    i[0] for i in list_route],
                lon=[
                    i[1] for i in list_route],
                mode='markers+lines',
                marker={
                    'size': 8}))
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 40}, mapbox={
                      'zoom': 5, "center": {'lat': 44, 'lon': 0}})
    fig.update_layout(mapbox_style="open-street-map")
    return fig


def route_cost(route):
    distances = data["edge_weight"]
    tour = [0] + route + [0]

    return sum(distances[tour[idx]][tour[idx + 1]]
               for idx in range(len(tour) - 1))


def random_removal(state, rnd_state):
    """
    Removes a number of randomly selected customers from the passed-in solution.
    """
    destroyed = state.copy()

    for customer in rnd_state.choice(
        range(1, data["dimension"]), customers_to_remove, replace=False
    ):
        destroyed.unassigned.append(customer)
        route = destroyed.find_route(customer)
        route.remove(customer)

    return remove_empty_routes(destroyed)


def remove_empty_routes(state):
    """
    Remove empty routes after applying the destroy operator.
    """
    state.routes = [route for route in state.routes if len(route) != 0]
    return state


def greedy_repair(state, rnd_state):
    """
    Inserts the unassigned customers in the best route. If there are no
    feasible insertions, then a new route is created.
    """
    rnd_state.shuffle(state.unassigned)

    while len(state.unassigned) != 0:
        customer = state.unassigned.pop()
        route, idx = best_insert(customer, state)

        if route is not None:
            route.insert(idx, customer)
        else:
            state.routes.append([customer])

    return state


def best_insert(customer, state):
    """
    Finds the best feasible route and insertion idx for the customer.
    Return (None, None) if no feasible route insertions are found.
    """
    best_cost, best_route, best_idx = None, None, None

    for route in state.routes:
        for idx in range(len(route) + 1):

            if can_insert(customer, route):
                cost = insert_cost(customer, route, idx)

                if best_cost is None or cost < best_cost:
                    best_cost, best_route, best_idx = cost, route, idx

    return best_route, best_idx


def can_insert(customer, route):
    """
    Checks if inserting customer does not exceed vehicle capacity.
    """
    total = data["demand"][route].sum() + data["demand"][customer]
    return total <= data["capacity"]


def insert_cost(customer, route, idx):
    """
    Computes the insertion cost for inserting customer in route at idx.
    """
    dist = data["edge_weight"]
    pred = 0 if idx == 0 else route[idx - 1]
    succ = 0 if idx == len(route) else route[idx]

    # Increase in cost of adding customer, minus cost of removing old edge
    return dist[pred][customer] + dist[customer][succ] - dist[pred][succ]
