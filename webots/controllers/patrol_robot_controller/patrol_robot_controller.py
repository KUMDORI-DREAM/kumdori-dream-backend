import math

from controller import Robot

WAYPOINTS = [
    (2.0, 2.0),
    (2.0, -2.0),
    (-2.0, -2.0),
    (-2.0, 2.0),
]

ARRIVAL_RADIUS = 0.25
BASE_SPEED = 4.0
TURN_GAIN = 3.0
MAX_MOTOR_SPEED = 6.0

robot = Robot()
time_step = int(robot.getBasicTimeStep())

gps = robot.getDevice("gps")
gps.enable(time_step)

compass = robot.getDevice("compass")
compass.enable(time_step)

left_motors = [robot.getDevice("front_left_motor"), robot.getDevice("rear_left_motor")]
right_motors = [robot.getDevice("front_right_motor"), robot.getDevice("rear_right_motor")]

for motor in left_motors + right_motors:
    motor.setPosition(float("inf"))
    motor.setVelocity(0.0)


def wrap_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def heading_from_compass(north: tuple[float, float, float]) -> float:
    bearing = math.atan2(north[1], north[0])
    return wrap_angle(math.pi / 2 - bearing)


waypoint_index = 0

while robot.step(time_step) != -1:
    position = gps.getValues()
    north = compass.getValues()

    x, y = position[0], position[1]
    heading = heading_from_compass(north)

    target_x, target_y = WAYPOINTS[waypoint_index]
    dx, dy = target_x - x, target_y - y
    distance = math.hypot(dx, dy)

    if distance < ARRIVAL_RADIUS:
        waypoint_index = (waypoint_index + 1) % len(WAYPOINTS)
        print(f"[patrol-robot-01] reached waypoint {waypoint_index}, position=({x:.2f}, {y:.2f})")
        continue

    target_angle = math.atan2(dy, dx)
    heading_error = wrap_angle(target_angle - heading)

    turn = max(-1.0, min(1.0, TURN_GAIN * heading_error))
    forward = BASE_SPEED * max(0.0, 1.0 - abs(heading_error) / (math.pi / 2))

    left_speed = max(-MAX_MOTOR_SPEED, min(MAX_MOTOR_SPEED, forward - turn * TURN_GAIN))
    right_speed = max(-MAX_MOTOR_SPEED, min(MAX_MOTOR_SPEED, forward + turn * TURN_GAIN))

    for motor in left_motors:
        motor.setVelocity(left_speed)
    for motor in right_motors:
        motor.setVelocity(right_speed)
