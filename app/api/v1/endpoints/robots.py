from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.robot import Robot, RobotTelemetry, SafetyEvent
from app.schemas.robot import HeartbeatIn, RobotCreateIn, RobotOut, SafetyEventIn, SafetyEventOut

router = APIRouter(prefix="/robots", tags=["robots"])


@router.post("", response_model=RobotOut, status_code=201)
async def create_robot(payload: RobotCreateIn, db: AsyncSession = Depends(get_db)) -> Robot:
    if await db.get(Robot, payload.id) is not None:
        raise HTTPException(status_code=409, detail="robot already registered")

    robot = Robot(id=payload.id, name=payload.name)
    db.add(robot)
    await db.commit()
    await db.refresh(robot)
    return robot


@router.post("/{robot_id}/heartbeat", response_model=RobotOut)
async def send_heartbeat(
    robot_id: str, payload: HeartbeatIn, db: AsyncSession = Depends(get_db)
) -> Robot:
    now = datetime.now(UTC)

    robot = await db.get(Robot, robot_id)
    if robot is None:
        robot = Robot(id=robot_id, status=payload.status, battery=payload.battery, last_seen=now)
        db.add(robot)
    else:
        robot.status = payload.status
        robot.battery = payload.battery
        robot.last_seen = now
    robot.current_node = payload.current_node
    robot.target_node = payload.target_node

    db.add(
        RobotTelemetry(
            robot_id=robot_id,
            x=payload.x,
            y=payload.y,
            battery=payload.battery,
            status=payload.status,
        )
    )

    await db.commit()
    await db.refresh(robot)
    return robot


@router.get("", response_model=list[RobotOut])
async def list_robots(db: AsyncSession = Depends(get_db)) -> list[Robot]:
    result = await db.execute(select(Robot).order_by(Robot.id))
    return list(result.scalars().all())


@router.get("/{robot_id}", response_model=RobotOut)
async def get_robot(robot_id: str, db: AsyncSession = Depends(get_db)) -> Robot:
    robot = await db.get(Robot, robot_id)
    if robot is None:
        raise HTTPException(status_code=404, detail="robot not found")
    return robot


@router.post("/{robot_id}/safety-events", response_model=SafetyEventOut)
async def create_safety_event(
    robot_id: str, payload: SafetyEventIn, db: AsyncSession = Depends(get_db)
) -> SafetyEvent:
    robot = await db.get(Robot, robot_id)
    if robot is None:
        raise HTTPException(status_code=404, detail="robot not found")
    event = SafetyEvent(robot_id=robot_id, **payload.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/{robot_id}/safety-events", response_model=list[SafetyEventOut])
async def list_safety_events(
    robot_id: str, db: AsyncSession = Depends(get_db)
) -> list[SafetyEvent]:
    result = await db.execute(
        select(SafetyEvent)
        .where(SafetyEvent.robot_id == robot_id)
        .order_by(SafetyEvent.created_at.desc())
    )
    return list(result.scalars().all())
