from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.warehouse import WarehouseEdge, WarehouseNode
from app.schemas.route import WarehouseEdgeIn, WarehouseNodeIn

router = APIRouter(prefix="/warehouse", tags=["warehouse"])


@router.post("/nodes", status_code=201)
async def create_node(payload: WarehouseNodeIn, db: AsyncSession = Depends(get_db)):
    node = WarehouseNode(**payload.model_dump())
    db.add(node)
    await db.commit()
    return payload


@router.post("/edges", status_code=201)
async def create_edge(payload: WarehouseEdgeIn, db: AsyncSession = Depends(get_db)):
    edge = WarehouseEdge(**payload.model_dump())
    db.add(edge)
    await db.commit()
    return payload


@router.get("/nodes")
async def list_nodes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WarehouseNode).order_by(WarehouseNode.id))
    return list(result.scalars().all())


@router.get("/edges")
async def list_edges(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WarehouseEdge).order_by(WarehouseEdge.id))
    return list(result.scalars().all())
