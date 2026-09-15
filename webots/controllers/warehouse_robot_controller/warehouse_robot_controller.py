"""그래프 노드 좌표를 따라 창고 경로를 주행하는 컨트롤러."""
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
BASE_SPEED = 5.2
TURN_GAIN = 4.0
MAX_MOTOR_SPEED = 6.0
# 전방 센서는 감지된 물체가 없으면 0을, 가까운 장애물이 있으면
# 양수 값을 반환한다. 시험 장애물 앞에서 멈추도록 작은 임계값을 사용한다.
OBSTACLE_THRESHOLD = 50.0
AVOIDANCE_REVERSE_S = 0.45
AVOIDANCE_TURN_S = 0.7
AVOIDANCE_FORWARD_S = 0.8
OBSTACLE_HEADING_TOLERANCE = 0.55

robot = Robot()
time_step = int(robot.getBasicTimeStep())
print(f"[DEBUG] controller initialized, timestep={time_step}", flush=True)
gps = robot.getDevice("gps")
compass = robot.getDevice("compass")
front_sensor = robot.getDevice("front_distance_sensor")
gps.enable(time_step)
compass.enable(time_step)
front_sensor.enable(time_step)
left_motors = [robot.getDevice("front_left_motor"), robot.getDevice("rear_left_motor")]
right_motors = [robot.getDevice("front_right_motor"), robot.getDevice("rear_right_motor")]
for motor in left_motors + right_motors:
    motor.setPosition(float("inf"))
print("[DEBUG] devices initialized, entering simulation loop", flush=True)

# 첫 번째 waypoint 구간이 시험 장애물을 통과하는 순환 경로를 주행한다.
agent = EdgeAgent(ROBOT_ID)
route = ["A1", "A2", "B2", "B1"]
route_index = 0
avoidance_until = 0.0
avoidance_reverse_until = 0.0
avoidance_forward_until = 0.0
avoidance_direction = 1.0
last_debug_s = -1.0

def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))

while robot.step(time_step) != -1:
    now = robot.getTime()
    x, y = gps.getValues()[:2]
    north = compass.getValues()
    heading = wrap(math.pi / 2 - math.atan2(north[1], north[0]))
    sensor_value = front_sensor.getValue()
    target_node = route[route_index]
    target_x, target_y = NODE_COORDINATES[target_node]
    distance = math.hypot(target_x - x, target_y - y)
    error = wrap(math.atan2(target_y - y, target_x - x) - heading)
    if now - last_debug_s >= 1.0:
        print(
            f"[DEBUG] loop tick t={now:.2f}, position=({x:.2f}, {y:.2f}), "
            f"sensor={sensor_value:.1f}",
            flush=True,
        )
        last_debug_s = now
    if now < avoidance_reverse_until:
        left = -BASE_SPEED
        right = -BASE_SPEED
        for motor in left_motors:
            motor.setVelocity(left)
        for motor in right_motors:
            motor.setVelocity(right)
        agent.send_heartbeat(now, x, y, "WAITING")
        continue

    if now < avoidance_until:
        left = -MAX_MOTOR_SPEED * avoidance_direction
        right = MAX_MOTOR_SPEED * avoidance_direction
        for motor in left_motors:
            motor.setVelocity(left)
        for motor in right_motors:
            motor.setVelocity(right)
        agent.send_heartbeat(now, x, y, "WAITING")
        continue

    if now < avoidance_forward_until:
        left = BASE_SPEED
        right = BASE_SPEED
        for motor in left_motors:
            motor.setVelocity(left)
        for motor in right_motors:
            motor.setVelocity(right)
        agent.send_heartbeat(now, x, y, "WAITING")
        continue

    # 경로 방향과 무관한 물체가 센서에 잡혔을 때는 회피하지 않는다.
    # 시작 위치에서 시험 장애물이 센서 범위에 들어오는 오탐을 방지한다.
    if (
        sensor_value >= OBSTACLE_THRESHOLD
        and abs(error) <= OBSTACLE_HEADING_TOLERANCE
    ):
        blocked_node = route[route_index]
        if blocked_node == "A2":
            # A1-A2 통로가 막히면 B1-B2를 거쳐 A2로 우회한다.
            route = ["B1", "B2", "A2"]
            route_index = 0
        else:
            route_index = (route_index + 1) % len(route)
        print(
            f"[DEBUG] obstacle near {blocked_node}, detouring to {route[route_index]}",
            flush=True,
        )
        avoidance_reverse_until = now + AVOIDANCE_REVERSE_S
        avoidance_until = avoidance_reverse_until + AVOIDANCE_TURN_S
        avoidance_forward_until = avoidance_until + AVOIDANCE_FORWARD_S
        for motor in left_motors + right_motors:
            motor.setVelocity(0.0)
        agent.send_heartbeat(now, x, y, "WAITING")
        continue

    if distance < ARRIVAL_RADIUS:
        for motor in left_motors + right_motors:
            motor.setVelocity(0.0)
        route_index = (route_index + 1) % len(route)
        agent.send_heartbeat(
            now, x, y, "IDLE", current_node=target_node,
            target_node=route[route_index],
        )
        continue
    turn = max(-3.0, min(3.0, TURN_GAIN * error))
    alignment = max(0.0, math.cos(error))
    # waypoint에 가까워질수록 전진 속도를 줄인다. 최소 전진 속도가 남아
    # 있으면 waypoint를 지나쳐 창고 벽을 시험 장애물로 잘못 감지할 수 있다.
    forward = min(BASE_SPEED, distance * 2.0) * alignment
    left = max(-MAX_MOTOR_SPEED, min(MAX_MOTOR_SPEED, forward - turn))
    right = max(-MAX_MOTOR_SPEED, min(MAX_MOTOR_SPEED, forward + turn))
    for motor in left_motors:
        motor.setVelocity(left)
    for motor in right_motors:
        motor.setVelocity(right)
    agent.send_heartbeat(
        now, x, y, "MOVING", current_node=target_node,
        target_node=route[(route_index + 1) % len(route)],
    )
