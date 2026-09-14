from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RobotStatus:
    ONLINE = "ONLINE"
    IDLE = "IDLE"
    MOVING = "MOVING"
    REPLANNING = "REPLANNING"
    WAITING = "WAITING"
    ALERT = "ALERT"
    OFFLINE = "OFFLINE"

    ALL = (ONLINE, IDLE, MOVING, REPLANNING, WAITING, ALERT, OFFLINE)


class Robot(Base):
    __tablename__ = "robots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=RobotStatus.OFFLINE, server_default=RobotStatus.OFFLINE
    )
    battery: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_node: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_node: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    telemetry: Mapped[list["RobotTelemetry"]] = relationship(
        back_populates="robot", cascade="all, delete-orphan"
    )


class RobotTelemetry(Base):
    __tablename__ = "robot_telemetry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    robot_id: Mapped[str] = mapped_column(
        ForeignKey("robots.id", ondelete="CASCADE"), index=True, nullable=False
    )
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    battery: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    robot: Mapped[Robot] = relationship(back_populates="telemetry")


class SafetyEventType:
    PERSON_IN_PATH = "PERSON_IN_PATH"
    OBJECT_ON_AISLE = "OBJECT_ON_AISLE"
    AISLE_BLOCKED = "AISLE_BLOCKED"
    FALL = "FALL"

    ALL = (PERSON_IN_PATH, OBJECT_ON_AISLE, AISLE_BLOCKED, FALL)


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    robot_id: Mapped[str] = mapped_column(ForeignKey("robots.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="WARNING")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolved: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
