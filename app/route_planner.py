from heapq import heappop, heappush


def a_star(graph, coordinates, start: str, goal: str) -> list[str]:
    """Return the least-cost route through a warehouse graph."""
    if start not in coordinates or goal not in coordinates:
        raise ValueError("start and goal must exist in the warehouse graph")
    queue = [(0.0, start)]
    came_from = {}
    cost_so_far = {start: 0.0}

    def heuristic(node: str) -> float:
        x1, y1 = coordinates[node]
        x2, y2 = coordinates[goal]
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    while queue:
        _, current = heappop(queue)
        if current == goal:
            route = [current]
            while current in came_from:
                current = came_from[current]
                route.append(current)
            return route[::-1]
        for neighbor, edge_cost in graph.get(current, []):
            new_cost = cost_so_far[current] + edge_cost
            if new_cost < cost_so_far.get(neighbor, float("inf")):
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                heappush(queue, (new_cost + heuristic(neighbor), neighbor))
    raise ValueError("no route exists between the requested warehouse nodes")
