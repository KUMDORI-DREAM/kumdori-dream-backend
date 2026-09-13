from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RobotStatus:
    ONLINE = "ONLINE"
    PATROLLING = "PATROLLING"
    ALERT = "ALERT"
    MANUAL_CONTROL = "MANUAL_CONTROL"
    OFFLINE = "OFFLINE"


class Robot(Base):
    __tablename__ = "robots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=RobotStatus.OFFLINE, server_default=RobotStatus.OFFLINE
    )
    battery: Mapped[float | None] = mapped_column(Float, nullable=True)
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
