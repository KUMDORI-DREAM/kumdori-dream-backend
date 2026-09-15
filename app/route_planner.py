from heapq import heappop, heappush


def a_star(graph, coordinates, start: str, goal: str) -> list[str]:
    """창고 그래프에서 비용이 가장 낮은 경로를 반환한다."""
    if start not in coordinates or goal not in coordinates:
        raise ValueError("start and goal must exist in the warehouse graph")
    for node, edges in graph.items():
        if node not in coordinates:
            raise ValueError(f"node {node!r} must have coordinates")
        for neighbor, edge_cost in edges:
            if neighbor not in coordinates:
                raise ValueError(f"node {neighbor!r} must have coordinates")
            if edge_cost < 0:
                raise ValueError("edge costs must be non-negative")
    queue = [(0.0, start)]
    came_from = {}
    cost_so_far = {start: 0.0}

    def heuristic(node: str) -> float:
        x1, y1 = coordinates[node]
        x2, y2 = coordinates[goal]
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    while queue:
        _, current = heappop(queue)
        for neighbor, edge_cost in graph.get(current, []):
            new_cost = cost_so_far[current] + edge_cost
            if new_cost < cost_so_far.get(neighbor, float("inf")):
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                heappush(queue, (new_cost + heuristic(neighbor), neighbor))
    if goal not in cost_so_far:
        raise ValueError("no route exists between the requested warehouse nodes")
    route = [goal]
    current = goal
    while current in came_from:
        current = came_from[current]
        route.append(current)
    return route[::-1]
