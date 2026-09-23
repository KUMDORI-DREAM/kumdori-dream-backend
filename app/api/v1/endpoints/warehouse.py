from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.warehouse import WarehouseEdge, WarehouseNode
from app.schemas.route import WarehouseEdgeIn, WarehouseNodeIn, WarehouseNodePatch

router = APIRouter(prefix="/warehouse", tags=["warehouse"])


@router.post("/nodes", status_code=201)
async def create_node(payload: WarehouseNodeIn, db: AsyncSession = Depends(get_db)):
    if await db.get(WarehouseNode, payload.id) is not None:
        raise HTTPException(status_code=409, detail="warehouse node already exists")
    node = WarehouseNode(**payload.model_dump())
    db.add(node)
    await db.commit()
    return payload


@router.patch("/nodes/{node_id}")
async def update_node(
    node_id: str, payload: WarehouseNodePatch, db: AsyncSession = Depends(get_db)
):
    node = await db.get(WarehouseNode, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="warehouse node not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(node, field, value)
    await db.commit()
    await db.refresh(node)
    return node


@router.delete("/nodes/{node_id}", status_code=204)
async def delete_node(node_id: str, db: AsyncSession = Depends(get_db)):
    node = await db.get(WarehouseNode, node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="warehouse node not found")
    await db.delete(node)
    await db.commit()


@router.post("/edges", status_code=201)
async def create_edge(payload: WarehouseEdgeIn, db: AsyncSession = Depends(get_db)):
    edge = WarehouseEdge(**payload.model_dump())
    db.add(edge)
    await db.commit()
    await db.refresh(edge)
    return edge


@router.delete("/edges/{edge_id}", status_code=204)
async def delete_edge(edge_id: int, db: AsyncSession = Depends(get_db)):
    edge = await db.get(WarehouseEdge, edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="warehouse edge not found")
    await db.delete(edge)
    await db.commit()


@router.get("/nodes")
async def list_nodes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WarehouseNode).order_by(WarehouseNode.id))
    return list(result.scalars().all())


@router.get("/edges")
async def list_edges(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WarehouseEdge).order_by(WarehouseEdge.id))
    return list(result.scalars().all())
