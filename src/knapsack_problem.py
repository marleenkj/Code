from ortools.linear_solver import pywraplp
import sys
sys.path.append('..')


def knapsack(list_customers, list_weights, bin_capacity):
    """
    
    """
    # Create the mip solver with the SCIP backend.
    data = {}
    data['weights'] = list_weights
    data['items'] = list(range(len(data['weights'])))
    data['bins'] = data['items']
    data['bin_capacity'] = bin_capacity

    solver = pywraplp.Solver.CreateSolver('SCIP')

    if not solver:
        return

    # Variables
    # x[i, j] = 1 if item i is packed in bin j.
    x = {}
    for i in data['items']:
        for j in data['bins']:
            x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

    # y[j] = 1 if bin j is used.
    y = {}
    for j in data['bins']:
        y[j] = solver.IntVar(0, 1, 'y[%i]' % j)

    # Constraints
    # Each item must be in exactly one bin.
    for i in data['items']:
        solver.Add(sum(x[i, j] for j in data['bins']) == 1)

    # The amount packed in each bin cannot exceed its capacity.
    for j in data['bins']:
        solver.Add(sum(x[(i, j)] * data['weights'][i]
                       for i in data['items']) <= y[j] * data['bin_capacity'])

    # Objective: minimize the number of bins used.
    solver.Minimize(solver.Sum([y[j] for j in data['bins']]))

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        solution = []
        num_bins = 0
        for j in data['bins']:
            if y[j].solution_value() == 1:
                bin_items = []
                bin_weight = 0
                for i in data['items']:
                    if x[i, j].solution_value() > 0:
                        bin_items.append(i)
                        bin_weight += data['weights'][i]
                if bin_items:
                    num_bins += 1
                    print('Bin number', j)
                    print('  Items packed:', bin_items)
                    print('  Total weight:', bin_weight)
                    print()
                    solution.append(bin_items)
        clients_per_truck = []
        for i in range(len(solution)):
            clients_per_truck.append(
                [{v: k for v, k in enumerate(list_customers)}.get(a) for a in solution[i]])
        print()
        print('Number of bins used:', num_bins)
        print('Time = ', solver.WallTime(), ' milliseconds')
    else:
        print('The problem does not have an optimal solution.')
    return clients_per_truck
