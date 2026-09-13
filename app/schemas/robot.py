from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.robot import RobotStatus


class HeartbeatIn(BaseModel):
    x: float
    y: float
    status: str = RobotStatus.PATROLLING
    battery: float | None = None


class RobotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    battery: float | None
    last_seen: datetime | None
    created_at: datetime


class TelemetryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    robot_id: str
    x: float
    y: float
    battery: float | None
    status: str
    timestamp: datetime
