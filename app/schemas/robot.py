from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.robot import RobotStatus


class HeartbeatIn(BaseModel):
    x: float
    y: float
    status: str = RobotStatus.MOVING
    battery: float | None = None
    current_node: str | None = None
    target_node: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in RobotStatus.ALL:
            raise ValueError(f"unsupported robot status: {value}")
        return value


class RobotCreateIn(BaseModel):
    id: str
    name: str | None = None


class RobotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None
    status: str
    battery: float | None
    last_seen: datetime | None
    created_at: datetime
    current_node: str | None
    target_node: str | None


class RobotPositionEvent(BaseModel):
    robot_id: str
    x: float
    y: float
    status: str
    battery: float | None = None
    current_node: str | None = None
    target_node: str | None = None


class TelemetryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    robot_id: str
    x: float
    y: float
    battery: float | None
    status: str
    timestamp: datetime


class SafetyEventIn(BaseModel):
    event_type: str
    severity: str = "WARNING"
    description: str | None = None
    x: float | None = None
    y: float | None = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, value: str) -> str:
        from app.models.robot import SafetyEventType

        if value not in SafetyEventType.ALL:
            raise ValueError(f"unsupported safety event type: {value}")
        return value


class SafetyEventOut(SafetyEventIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    robot_id: str
    resolved: bool
    created_at: datetime
