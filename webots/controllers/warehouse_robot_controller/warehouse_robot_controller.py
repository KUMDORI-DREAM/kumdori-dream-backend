"""Warehouse route executor. The route is supplied as graph node coordinates."""
import math
import os

from controller import Robot
from edge_agent import EdgeAgent

ROBOT_ID = os.environ.get("KUMDORI_ROBOT_ID", "warehouse-robot-01")
WAREHOUSE_GRAPH = {
    "A1": [("A2", 4.0), ("B1", 4.0)],
    "A2": [("A1", 4.0), ("B2", 4.0)],
    "B1": [("A1", 4.0), ("B2", 4.0)],
    "B2": [("A2", 4.0), ("B1", 4.0)],
}
NODE_COORDINATES = {"A1": (2.0, 2.0), "A2": (2.0, -2.0), "B1": (-2.0, 2.0), "B2": (-2.0, -2.0)}


def a_star(start, goal):
    open_nodes = [(0.0, start)]
    came_from = {}
    cost = {start: 0.0}
    while open_nodes:
        _, current = min(open_nodes)
        open_nodes.remove((_, current))
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]
        for neighbor, edge_cost in WAREHOUSE_GRAPH[current]:
            new_cost = cost[current] + edge_cost
            if new_cost < cost.get(neighbor, float("inf")):
                cost[neighbor] = new_cost
                came_from[neighbor] = current
                gx, gy = NODE_COORDINATES[goal]
                nx, ny = NODE_COORDINATES[neighbor]
                open_nodes.append((new_cost + math.hypot(nx - gx, ny - gy), neighbor))
    return []
ARRIVAL_RADIUS = 0.25
BASE_SPEED = 4.0
TURN_GAIN = 3.0
MAX_MOTOR_SPEED = 6.0

robot = Robot()
time_step = int(robot.getBasicTimeStep())
gps = robot.getDevice("gps")
compass = robot.getDevice("compass")
gps.enable(time_step)
compass.enable(time_step)
left_motors = [robot.getDevice("front_left_motor"), robot.getDevice("rear_left_motor")]
right_motors = [robot.getDevice("front_right_motor"), robot.getDevice("rear_right_motor")]
for motor in left_motors + right_motors:
    motor.setPosition(float("inf"))

agent = EdgeAgent(ROBOT_ID)
route = a_star("A1", "B2")
route_index = 0

def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))

while robot.step(time_step) != -1:
    x, y = gps.getValues()[:2]
    north = compass.getValues()
    heading = wrap(math.pi / 2 - math.atan2(north[1], north[0]))
    target_node = route[route_index]
    target_x, target_y = NODE_COORDINATES[target_node]
    if math.hypot(target_x - x, target_y - y) < ARRIVAL_RADIUS:
        route_index = (route_index + 1) % len(route)
        continue
    error = wrap(math.atan2(target_y - y, target_x - x) - heading)
    turn = max(-1.0, min(1.0, TURN_GAIN * error))
    forward = BASE_SPEED * max(0.0, 1.0 - abs(error) / (math.pi / 2))
    left = max(-MAX_MOTOR_SPEED, min(MAX_MOTOR_SPEED, forward - turn * TURN_GAIN))
    right = max(-MAX_MOTOR_SPEED, min(MAX_MOTOR_SPEED, forward + turn * TURN_GAIN))
    for motor in left_motors:
        motor.setVelocity(left)
    for motor in right_motors:
        motor.setVelocity(right)
    agent.send_heartbeat(
        robot.getTime(), x, y, "MOVING", current_node=target_node,
        target_node=route[(route_index + 1) % len(route)],
    )
