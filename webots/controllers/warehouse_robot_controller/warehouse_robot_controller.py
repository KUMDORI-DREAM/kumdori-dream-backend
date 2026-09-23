"""그래프 노드 좌표를 따라 창고 경로를 주행하는 컨트롤러."""
import json
import math
import os
import urllib.error
import urllib.request

from controller import Robot
from edge_agent import DEFAULT_BACKEND_URL, EdgeAgent
from vision_client import PersonPathDetector

ROBOT_ID = os.environ.get("KUMDORI_ROBOT_ID", "warehouse-robot-01")

# 백엔드 연결이 안 될 때만 쓰는 최소 대체 그래프. 평소에는 백엔드의
# WarehouseNode/Edge가 대시보드와 컨트롤러가 공유하는 단일 맵 소스다.
FALLBACK_WAREHOUSE_GRAPH = {
    "A1": [("A2", 4.0), ("B1", 4.0)],
    "A2": [("A1", 4.0), ("B2", 4.0)],
    "B1": [("A1", 4.0), ("B2", 4.0)],
    "B2": [("A2", 4.0), ("B1", 4.0)],
}
FALLBACK_NODE_COORDINATES = {
    "A1": (2.0, 2.0),
    "A2": (2.0, -2.0),
    "B1": (-2.0, 2.0),
    "B2": (-2.0, -2.0),
}


def fetch_warehouse_graph(backend_url: str = DEFAULT_BACKEND_URL, timeout_s: float = 3.0):
    """백엔드의 WarehouseNode/Edge를 읽어 A* 그래프와 좌표 dict를 만든다.

    백엔드가 아직 안 떠 있거나 응답이 없으면 컨트롤러 전체가 멈추지
    않도록 하드코딩된 fallback 그래프로 내려간다.
    """
    try:
        with urllib.request.urlopen(
            f"{backend_url}/api/v1/warehouse/nodes", timeout=timeout_s
        ) as resp:
            nodes = json.loads(resp.read().decode("utf-8"))
        with urllib.request.urlopen(
            f"{backend_url}/api/v1/warehouse/edges", timeout=timeout_s
        ) as resp:
            edges = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"[warehouse-graph] backend fetch failed, using fallback graph: {exc}", flush=True)
        return dict(FALLBACK_WAREHOUSE_GRAPH), dict(FALLBACK_NODE_COORDINATES)

    if not nodes or not edges:
        print("[warehouse-graph] backend graph is empty, using fallback graph", flush=True)
        return dict(FALLBACK_WAREHOUSE_GRAPH), dict(FALLBACK_NODE_COORDINATES)

    coordinates = {node["id"]: (node["x"], node["y"]) for node in nodes}
    graph = {node_id: [] for node_id in coordinates}
    for edge in edges:
        if edge.get("blocked"):
            continue
        from_node, to_node, cost = edge["from_node"], edge["to_node"], edge["cost"]
        if from_node not in graph or to_node not in graph:
            continue
        graph[from_node].append((to_node, cost))
        graph[to_node].append((from_node, cost))
    return graph, coordinates


WAREHOUSE_GRAPH, NODE_COORDINATES = fetch_warehouse_graph()


def a_star(start, goal, blocked_edges=()):
    blocked_edges = set(blocked_edges)
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
            if (current, neighbor) in blocked_edges:
                continue
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
# 양수 값을 반환한다. 감속·정지·통로 차단 판단을 단계적으로 적용한다.
OBSTACLE_WARNING_THRESHOLD = 20.0
OBSTACLE_STOP_THRESHOLD = 50.0
OBSTACLE_BLOCK_THRESHOLD_S = 1.0
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
front_camera = robot.getDevice("front_camera")
gps.enable(time_step)
compass.enable(time_step)
front_sensor.enable(time_step)
front_camera.enable(time_step)
detect_interval_s = float(os.environ.get("KUMDORI_DETECT_INTERVAL_S", "0.3"))
left_motors = [robot.getDevice("front_left_motor"), robot.getDevice("rear_left_motor")]
right_motors = [robot.getDevice("front_right_motor"), robot.getDevice("rear_right_motor")]
for motor in left_motors + right_motors:
    motor.setPosition(float("inf"))
print("[DEBUG] devices initialized, entering simulation loop", flush=True)

# 첫 번째 waypoint 구간이 시험 장애물을 통과하는 순환 경로를 주행한다.
agent = EdgeAgent(ROBOT_ID)
detector = PersonPathDetector(
    on_person_in_path=lambda px, py: agent.send_safety_event(
        "PERSON_IN_PATH", px, py, description="YOLO 사람 감지"
    )
)
default_route = ["A1", "A2", "B2", "B1"]
route = default_route if all(n in NODE_COORDINATES for n in default_route) else list(NODE_COORDINATES)
route_index = 0
avoidance_until = 0.0
avoidance_reverse_until = 0.0
avoidance_forward_until = 0.0
avoidance_direction = 1.0
obstacle_started_at = None
last_debug_s = -1.0
last_detect_s = -detect_interval_s

def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))

while robot.step(time_step) != -1:
    now = robot.getTime()
    x, y = gps.getValues()[:2]
    north = compass.getValues()
    heading = wrap(math.pi / 2 - math.atan2(north[1], north[0]))
    sensor_value = front_sensor.getValue()
    if now - last_detect_s >= detect_interval_s:
        last_detect_s = now
        detector.submit_frame(
            now, front_camera.getImage(), front_camera.getWidth(), front_camera.getHeight(), x, y
        )
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
    path_obstacle = (
        sensor_value >= OBSTACLE_WARNING_THRESHOLD
        and abs(error) <= OBSTACLE_HEADING_TOLERANCE
    )
    if path_obstacle:
        if obstacle_started_at is None:
            obstacle_started_at = now
        if sensor_value < OBSTACLE_STOP_THRESHOLD:
            # 경고 구간에서는 감속만 하고 일시 장애물 여부를 계속 관찰한다.
            obstacle_speed_scale = 0.45
        else:
            # 정지 구간에서는 충돌을 막기 위해 로봇을 먼저 멈춘다.
            for motor in left_motors + right_motors:
                motor.setVelocity(0.0)
            if now - obstacle_started_at < OBSTACLE_BLOCK_THRESHOLD_S:
                agent.send_heartbeat(now, x, y, "WAITING")
                continue
            obstacle_speed_scale = 0.0
    else:
        obstacle_started_at = None
        obstacle_speed_scale = 1.0

    if path_obstacle and now - obstacle_started_at >= OBSTACLE_BLOCK_THRESHOLD_S:
        blocked_node = route[route_index]
        # 현재 구간을 차단하고 같은 목적지까지 A* 경로를 다시 계산한다.
        previous_node = route[route_index - 1] if route_index else route[-1]
        try:
            replanned_route = a_star(
                previous_node,
                blocked_node,
                blocked_edges={(previous_node, blocked_node)},
            )
            route = replanned_route[1:]
            route_index = 0
        except ValueError:
            # 대체 경로가 없으면 다음 순찰 지점을 시도한다.
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
    forward = min(BASE_SPEED, distance * 2.0) * alignment * obstacle_speed_scale
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
